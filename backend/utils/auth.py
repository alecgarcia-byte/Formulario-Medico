"""
utils/auth.py
-------------
Dependencias de autenticación para los endpoints del panel admin.

El panel NO usa login de usuario/contraseña: se accede mediante una **URL
permitida** que incrusta un **token JWT de acceso único** firmado con
`JWT_SECRET`. Cada URL de acceso incluye `sub=admin`, `iat`, `exp` y un
`jti` único que permite su revocación.

Flujo:
1. El administrador emite una URL de acceso → `emitir_url_acceso()` genera un
   JWT firmado (con caducidad) y lo registra en `admin_sessions` para poder
   revocarlo si se filtra.
2. El usuario visita `/admin-<JWT>` o llama a `/api/admin/<JWT>/...`.
3. `admin_token_verificado` valida la firma (HS256), el vencimiento y que el
   `jti` no esté revocado. Si algo falla → 404 (sin revelar la existencia).

En desarrollo, si no hay JWT emitido se acepta `admin_token()` (la llave
estática) para mantener flujos de prueba sencillos; en producción SOLO se
acepta un JWT de acceso firmado y no revocado.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, Path, status

from .. import config
from ..utils.security import create_jwt, verify_jwt

# Duración por defecto de una URL de acceso (minutos). 60 * 24 * 30 = 30 días.
DIAS_ACCESO_POR_DEFECTO = 30


def _es_produccion() -> bool:
    return config.ES_PRODUCCION


def emitir_jwt_acceso(
    expira_minutos: int = DIAS_ACCESO_POR_DEFECTO * 24 * 60,
) -> str:
    """Genera un JWT de acceso único al panel admin (la 'URL permitida').

    Crea el token firmado con `sub=admin` y un `jti` único. Si la tabla de
    sesiones existe, registra la sesión para permitir revocación.

    Args:
        expira_minutos: vida del acceso (por defecto 30 días).

    Returns:
        El JWT listo para usarse como `/admin-<jwt>` o `/api/admin/<jwt>/...`.
    """
    jti = str(uuid.uuid4())
    token = create_jwt({"sub": "admin", "jti": jti}, expires_minutes=expira_minutos)
    _registrar_sesion(jti, expira_minutos)
    return token


def _registrar_sesion(jti: str, expira_minutos: int) -> None:
    """Persiste la sesión (jti) en `admin_sessions` si la tabla existe.

    Fallo silencioso: si la tabla no está disponible (p. ej. dev con SQLite
    o migración pendiente) la autenticación se basa solo en firma/expiración.
    """
    try:
        from .. import models
        from ..database import SessionLocal

        expira_en = datetime.now(UTC) + timedelta(minutes=expira_minutos)
        with SessionLocal() as db:
            db.add(
                models.AdminSession(
                    admin_user_id=None,
                    token_jti=jti,
                    expira_en=expira_en,
                    revocado=False,
                )
            )
            db.commit()
    except Exception:  # noqa: BLE001 - la sesión es un refuerzo, no un requisito
        pass


def _jti_revocado(jti: str) -> bool:
    """True si el jti está registrado y revocado en `admin_sessions`."""
    try:
        from .. import models
        from ..database import SessionLocal
        from sqlalchemy import select

        with SessionLocal() as db:
            sesion = db.scalar(
                select(models.AdminSession).where(
                    models.AdminSession.token_jti == jti
                )
            )
            return bool(sesion and sesion.revocado)
    except Exception:  # noqa: BLE001
        return False


def admin_token_verificado(
    token: str = Path(..., max_length=300),
) -> dict[str, Any]:
    """Verifica el token de acceso administrativo presente en la ruta.

    Estrategia (sin revelar información al fallar):
    1. Si es un JWT válido (firma HS256 + `exp` vigente + `sub=admin`), se
       acepta salvo que su `jti` esté revocado.
    2. En desarrollo, se acepta también el `admin_token()` estático
       (compatibilidad con la llave de la URL clásica).

    Raises:
        HTTPException (404): si el token no es válido, siempre con el mismo
            mensaje "no encontrado" para no filtrar la existencia del panel.
    """
    # 1) JWT de acceso firmado.
    payload = verify_jwt(token)
    if payload and payload.get("sub") == "admin":
        jti = payload.get("jti")
        if jti and _jti_revocado(jti):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado."
            )
        return {"sub": "admin", "jti": jti}

    # 2) Solo en desarrollo: llave estática clásica.
    if not _es_produccion() and os.getenv("ADMIN_TOKEN"):
        import hmac

        esperado = config.admin_token()
        if hmac.compare_digest(
            token.encode("utf-8"), esperado.encode("utf-8")
        ):
            return {"sub": "admin"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado."
    )