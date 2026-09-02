"""
utils/middleware.py
-------------------
Middlewares de seguridad para la aplicación FastAPI:
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy...).
- Rate limiting básico por IP (mitiga abuso/DDoS a nivel aplicación).

Implementados como ASGI puro (no BaseHTTPMiddleware) para evitar bugs
conocidos de Starlette y funcionar de forma confiable en Vercel serverless.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable, Optional

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# Configuración de rate limiting
TASA_MAX_REQUESTS = 60
TASA_VENTANA_SEGUNDOS = 60
_historial: defaultdict[str, deque] = defaultdict(deque)


SEGURIDAD_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' https://images.unsplash.com data:; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' data:; "
        "connect-src 'self' https://images.unsplash.com"
    ),
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer-when-downgrade",
    "X-XSS-Protection": "1; mode=block",
    "Cache-Control": "no-store",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SeguridadHeadersMiddleware:
    """Middleware ASGI puro que inyecta security headers y limita por IP."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        ip = self._obtener_ip(request)

        if self._limitar(ip):
            cuerpo = b"Too many requests. Tente novamente em instantes."
            await self._enviar_respuesta(
                scope, receive, send, status_code=429, cuerpo=cuerpo
            )
            return

        async def send_con_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for nombre, valor in SEGURIDAD_HEADERS.items():
                    headers.append((nombre.lower().encode("latin-1"),
                                    valor.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_con_headers)

    @staticmethod
    def _obtener_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"

    @staticmethod
    def _limitar(ip: str) -> bool:
        ahora = time.time()
        cola: deque = _historial[ip]

        while cola and (ahora - cola[0]) > TASA_VENTANA_SEGUNDOS:
            cola.popleft()

        if len(cola) >= TASA_MAX_REQUESTS:
            return True

        cola.append(ahora)
        return False

    @staticmethod
    async def _enviar_respuesta(
        scope: Scope,
        receive: Receive,
        send: Send,
        status_code: int,
        cuerpo: bytes,
    ) -> None:
        headers = [
            (b"content-type", b"text/plain; charset=utf-8"),
            (b"cache-control", b"no-store"),
        ]
        for nombre, valor in SEGURIDAD_HEADERS.items():
            headers.append(
                (nombre.lower().encode("latin-1"), valor.encode("latin-1"))
            )
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": cuerpo,
        })


# Alias de fábrica para registrar con add_middleware
def SeguridadMiddleware(app: ASGIApp) -> ASGIApp:
    return SeguridadHeadersMiddleware(app)
