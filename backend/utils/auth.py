"""
utils/auth.py
-------------
Dependencias de autenticación para los endpoints del panel admin.

El panel ya NO usa login de usuario/contraseña: se accede mediante una
**URL/llave secreta** (ADMIN_TOKEN) incrustada en la ruta. Los endpoints
`/api/admin/{token}/...` verifican el token contra `config.admin_token()`.
Si no coincide, la petición se rechaza como 404/401 sin revelar nada.
"""

from __future__ import annotations

import hmac
from typing import Any

from fastapi import HTTPException, Path, status

from .. import config


def admin_token_verificado(
    token: str = Path(..., max_length=200),
) -> dict[str, Any]:
    """Verifica el token administrativo presente en la ruta.

    Se compara en tiempo constante (hmac.compare_digest) para evitar
    ataques de temporización. Devuelve un payload simbólico si es válido.

    Raises:
        HTTPException (404): si el token no coincide, sin filtrar
            información (se devuelve "no encontrado").
    """
    esperado = config.admin_token()
    if not hmac.compare_digest(token.encode("utf-8"),
                               esperado.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não encontrado.",
        )
    return {"sub": "admin"}
