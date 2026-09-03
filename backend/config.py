"""
config.py
---------
Configuración centralizada del backend: carga de secretos y validación.

Regla de oro de seguridad:
- **Nunca** se hardcodean secretos en el código.
- **Local (desarrollo):** los secretos van en un archivo `.env` en la raíz,
  que NO se sube a git (ver .gitignore). Este módulo lo carga con `dotenv`.
- **Producción (Vercel):** los secretos se inyectan desde las Environment
  Variables de Vercel (no hay archivo). Si están presentes, se respetan.

La validación "fail-fast" garantiza que en producción el arranque falle si
falta un secreto imprescindible, en lugar de funcionar de forma insegura.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Cargamos el .env desde la raíz del proyecto (o backend/ si aplica).
# load_dotenv es idempotente: no pisa variables ya definidas en el entorno,
# así que en Vercel (variables del entorno) no altera nada.
_RAIZ = Path(__file__).resolve().parent.parent  # .../backend -> proyecto
for _posible in (_RAIZ, _RAIZ / "backend"):
    _env = _posible / ".env"
    if _env.exists():
        load_dotenv(_env, override=False)
        break


def _es_produccion() -> bool:
    return os.getenv("ENVIRONMENT", "").lower() in ("prod", "production")


ES_PRODUCCION = _es_produccion()


# --- Acceso a secretos con validación (central) ---------------------------


def _get_secreto(nombre: str, dev_default: str | None = None) -> str:
    """Lee un secreto; en desarrollo permite un valor por defecto explícito.

    Raises:
        RuntimeError: si no hay valor y no estamos en desarrollo con default.
    """
    valor = os.getenv(nombre)
    if valor:
        return valor
    if dev_default is not None and not ES_PRODUCCION:
        return dev_default
    raise RuntimeError(
        f"Variable de entorno '{nombre}' no configurada. "
        "Consulte docs/DEPLOY.md y backend/.env.example."
    )


def secret_key_aes() -> bytes:
    """Clave AES de 32 bytes en base64 (AES-256 estricto)."""
    secreto = _get_secreto("SECRET_KEY_AES")  # sin default: siempre requerida
    import base64

    try:
        clave = base64.b64decode(secreto, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("SECRET_KEY_AES no es base64 válido.") from exc
    if len(clave) != 32:
        raise RuntimeError(
            "SECRET_KEY_AES debe ser una clave de 32 bytes en base64 (AES-256)."
        )
    return clave


def jwt_secret() -> str:
    """Secreto de firma JWT (longitud mínima)."""
    secreto = _get_secreto("JWT_SECRET")  # sin default: siempre requerida
    if len(secreto) < 32:
        raise RuntimeError(
            "JWT_SECRET debe tener al menos 32 caracteres (use: openssl rand -hex 32)."
        )
    return secreto


def credenciales_admin() -> tuple[str, str]:
    """Devuelve (usuario, hash_bcrypt) del admin; valida su presencia.

    Se mantiene por compatibilidad, pero el acceso ya no usa usuario/
    contraseña: se autentica con `admin_token()` (URL/llave secreta).
    """
    usuario = _get_secreto("ADMIN_USER")   # sin default
    hash_pass = _get_secreto("ADMIN_PASSWORD_HASH")  # sin default
    if not hash_pass.startswith("$2"):
        raise RuntimeError(
            "ADMIN_PASSWORD_HASH debe ser un hash bcrypt (empieza con '$2')."
        )
    return usuario, hash_pass


def admin_token() -> str:
    """Token/llave secreta de acceso al panel admin (ADMIN_TOKEN).

    Es un secreto largo y aleatorio que actúa como URL y llave de acceso
    (sin usuario/contraseña). Si no se ha configurado (p. ej. en desarrollo
    sin `.env`), se genera uno efímero por proceso y se avisa por log.
    """
    valor = os.getenv("ADMIN_TOKEN")
    if valor and len(valor) >= 20:
        return valor
    # En desarrollo generamos uno aleatorio si falta; en producción falla.
    if not ES_PRODUCCION:
        import secrets as _secrets
        generado = _secrets.token_urlsafe(32)
        logging.getLogger("formulario").warning(
            "ADMIN_TOKEN no configurado: usando token temporal %s", generado
        )
        return generado
    raise RuntimeError(
        "Variable de entorno 'ADMIN_TOKEN' no configurada. "
        "Consulte docs/DEPLOY.md y .env.example."
    )


def frontend_url() -> str | None:
    """URL del frontend para CORS (opcional)."""
    return os.getenv("FRONTEND_URL") or None
