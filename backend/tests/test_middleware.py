"""
test_middleware.py
------------------
Pruebas del middleware de seguridad (headers y rate limiting).
"""

from __future__ import annotations

import time

from backend.utils import middleware as mw
from backend.utils.middleware import SEGURIDAD_HEADERS


class TestSeguridadHeaders:
    def test_headers_presentes_en_api(self, client):
        r = client.get("/api/health")
        for header in (
            "content-security-policy",
            "strict-transport-security",
            "x-frame-options",
            "x-content-type-options",
            "referrer-policy",
        ):
            assert header in r.headers, f"Falta header {header}"

    def test_csp_prohibe_script_inline(self):
        csp = SEGURIDAD_HEADERS["Content-Security-Policy"]
        assert "script-src 'self'" in csp
        # Aislamos la directiva script-src y verificamos que no admite inline.
        directivas = csp.split(";")
        script = next(
            d.strip() for d in directivas if d.strip().startswith("script-src")
        )
        assert "unsafe-inline" not in script

    def test_frame_options_deny(self):
        assert SEGURIDAD_HEADERS["X-Frame-Options"] == "DENY"

    def test_nosniff(self):
        assert SEGURIDAD_HEADERS["X-Content-Type-Options"] == "nosniff"

    def test_headers_tambien_en_errores(self, client):
        r = client.get("/api/ruta/que/no/existe")
        assert r.status_code == 404
        assert "x-content-type-options" in r.headers
        assert "content-security-policy" in r.headers


class TestRateLimit:
    def _ip_unica(self) -> str:
        """IP de prueba con ventana siempre fresca."""
        return "198.51.100." + str(int(time.time()) % 200 + 1)

    def test_limitar_bloquea_al_superar_limite(self):
        ip = self._ip_unica()
        mw._historial[ip].clear()
        bloqueado = False
        for _ in range(mw.TASA_MAX_REQUESTS + 3):
            if mw.SeguridadHeadersMiddleware._limitar(ip):
                bloqueado = True
                break
        assert bloqueado is True

    def test_no_bloquea_bajo_limite(self):
        ip = self._ip_unica()
        mw._historial[ip].clear()
        for _ in range(mw.TASA_MAX_REQUESTS - 1):
            assert mw.SeguridadHeadersMiddleware._limitar(ip) is False

    def test_ventana_expira(self):
        from collections import deque

        ip = self._ip_unica()
        mw._historial[ip] = deque()
        # Llenamos hasta el límite y verificamos bloqueo.
        for _ in range(mw.TASA_MAX_REQUESTS):
            mw.SeguridadHeadersMiddleware._limitar(ip)
        assert mw.SeguridadHeadersMiddleware._limitar(ip) is True
        # Simulamos que pasó la ventana: los timestamps quedan viejos.
        mw._historial[ip] = deque([time.time() - mw.TASA_VENTANA_SEGUNDOS - 1])
        assert mw.SeguridadHeadersMiddleware._limitar(ip) is False
