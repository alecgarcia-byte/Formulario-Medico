"""
utils/auth.py
-------------
Dependencias de autenticación para los endpoints del panel admin.

Protege los endpoints `/admin/*` exigiendo un JWT válido emitido tras el
login. Se usa como dependencia de FastAPI (Depends) en cada ruta admin.
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import verify_jwt

# Bearer token en el header Authorization.
_esquema = HTTPBearer(auto_error=False)


def admin_autenticado(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
) -> dict[str, Any]:
    """Verifica el JWT de administrador. Devuelve el payload si es válido.

    Raises:
        HTTPException (401/403): si falta el token o es inválido/expirado.
    """
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Token ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_jwt(credenciales.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Opcional: validar rol/claim si se reenvía. Por ahora basta `sub`.
    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado.",
        )

    return payload
