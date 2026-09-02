"""
utils/security.py
-----------------
Capas de seguridad del backend (alta prioridad): cifrado AES-256-GCM,
hashing bcrypt y JWT.

Principios aplicados:
- Ningún secreto hardcodeado: todo proviene de variables de entorno.
- AES-256 estricto (solo claves de 32 bytes; se rechazan claves débiles).
- Nonce aleatorio de 96 bits por operación (recomendado por GCM).
- AAD (associated data) para evitar usos cruzados de los datos cifrados.
- bcrypt con coste configurable y longitud acotada (evita DoS).
- Comparación de strings en tiempo constante (hmac.compare_digest).
- JWT HS256 con validación estricta de header, firma y reclamaciones.

Ventajas de usar AES-GCM vía `cryptography.hazmat` (no Fernet):
- Autenticación integrada (detección de manipulación).
- Nonce controlado de 96 bits.
- Flexibilidad sin el overhead/pre-requisitos de Fernet.

Variables de entorno requeridas (ver .env.example):
- SECRET_KEY_AES     : 32 bytes, en base64. Generar:  openssl rand -base64 32
- JWT_SECRET         : secreto de firma JWT.  Generar: openssl rand -hex 32
- ADMIN_USER         : usuario del panel admin.
- ADMIN_PASSWORD_HASH: hash bcrypt de la contraseña del panel admin.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any, Optional

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .. import config

logger = logging.getLogger(__name__)


class CifradoError(ValueError):
    """Error de cifrado/descifrado (datos corruptos, clave inválida...)."""


# Tamaños y constantes de seguridad ---------------------------------------
AES_KEY_LEN = 32           # 256 bits (AES-256)
AES_NONCE_LEN = 12         # 96 bits, recomendado por NIST para GCM
BCRYPT_COST = 12           # rounds de bcrypt
BCRYPT_MAX_PASSWORD_LEN = 72  # 72 bytes es el límite de bcrypt
JWT_ALGORITMO = "HS256"
JWT_EXPIRACION_MINUTOS = 120
# Reclamaciones JWT obligatorias
JWT_RECLAMOS_OBLIGATORIOS = ("exp", "iat", "sub")

_AAD = b"formulario-papa:v1"


# --- Cifrado AES-256-GCM -------------------------------------------------


def _clave_aes_bytes() -> bytes:
    """Devuelve la clave AES de exactamente 32 bytes (AES-256 estricto).

    La clave proviene de `config.secret_key_aes()`, que la lee de
    `SECRET_KEY_AES` (env var o `.env` local) y valida su longitud. Se
    rechazan claves de otra longitud (16/24 bytes) para no degradar
    el cifrado a AES-128/192.

    Raises:
        RuntimeError: si falta la variable o la clave no es AES-256.
    """
    return config.secret_key_aes()


def encrypt_field(plaintext: str) -> str:
    """Cifra un texto plano con AES-256-GCM.

    Formato de salida (base64):
        base64( nonce(12) + ciphertext + tag(16) )

    Args:
        plaintext: texto plano a cifrar (lo convierte a str).

    Returns:
        Cadena base64 del nonce + ciphertext autenticado.

    Raises:
        ValueError: si plaintext es None.
        RuntimeError: si la clave no está bien configurada.
    """
    if plaintext is None:
        raise CifradoError("No se puede cifrar un valor nulo.")
    texto = str(plaintext).encode("utf-8")
    if not texto:
        raise CifradoError("No se puede cifrar un valor vacío.")

    clave = _clave_aes_bytes()
    aesgcm = AESGCM(clave)
    # Nonce aleatorio de 96 bits (óptimo para GCM; nunca debe reutilizarse).
    nonce = os.urandom(AES_NONCE_LEN)

    ciphertext = aesgcm.encrypt(nonce, texto, _AAD)
    # El tag GCM de 16 bytes queda al final del ciphertext devuelto por la lib.
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(ciphertext_b64: str) -> str:
    """Descifra un valor producido por encrypt_field().

    Verifica autenticidad (AAD + tag GCM) antes de devolver el texto plano,
    de modo que datos alterados o con clave incorrecta fallan de forma segura.

    Risos:
        CifradoError: si el cifrado es corrupto o la autenticación falla.
    """
    try:
        data = base64.b64decode(ciphertext_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CifradoError("Cifrado corrupto.") from exc

    if len(data) <= AES_NONCE_LEN + 16:  # nonce + tag mínimo
        raise CifradoError("Cifrado con longitud inválida.")

    clave = _clave_aes_bytes()
    aesgcm = AESGCM(clave)

    nonce = data[:AES_NONCE_LEN]
    ciphertext = data[AES_NONCE_LEN:]

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, _AAD)
    except Exception as exc:  # noqa: BLE001 - GCM falla por autenticación
        raise CifradoError(
            "No se pudo descifrar (clave incorrecta o dato alterado)."
        ) from exc

    return plaintext.decode("utf-8")


# --- Hashing bcrypt (contraseña admin) -----------------------------------


def hash_password(password: str) -> str:
    """Genera un hash bcrypt de la contraseña (coste configurable)."""
    _validar_password_digest(password)
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_COST)
    ).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt en tiempo constante."""
    if not isinstance(password, str) or not isinstance(hashed, str):
        return False
    try:
        # bcrypt trunca a 72 bytes; validamos para evitar DoS por entrada larga.
        if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_LEN:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def _validar_password_digest(password: str) -> None:
    """Valida la contraseña antes de hashear (evita entradas extremas)."""
    if not isinstance(password, str):
        raise TypeError("La contraseña debe ser una cadena.")
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_LEN:
        raise ValueError(
            f"La contraseña no puede exceder {BCRYPT_MAX_PASSWORD_LEN} bytes."
        )


def es_password_admin(usuario: str, password: str) -> bool:
    """Valida credenciales de administrador de forma segura.

    Compara el usuario en tiempo constante y verifica la contraseña
    contra el hash bcrypt almacenado en ADMIN_PASSWORD_HASH.
    Devuelve False en cualquier fallo sin filtrar información.
    """
    try:
        expected_user, expected_hash = config.credenciales_admin()
    except RuntimeError:
        return False

    if not isinstance(usuario, str) or not isinstance(password, str):
        return False

    usuario_ok = hmac.compare_digest(usuario.encode("utf-8"),
                                     expected_user.encode("utf-8"))
    if not usuario_ok:
        return False
    return verify_password(password, expected_hash)


# --- JWT (autenticación admin) -------------------------------------------


def _jwt_secret() -> str:
    return config.jwt_secret()


def _b64url_encode(obj: Any) -> str:
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segmento: str) -> dict[str, Any]:
    relleno = "=" * (-len(segmento) % 4)
    raw = base64.urlsafe_b64decode(segmento + relleno)
    return json.loads(raw.decode("utf-8"))


def _firmar(header: str, payload: str) -> str:
    signing_input = f"{header}.{payload}".encode("ascii")
    firma = hmac.new(
        _jwt_secret().encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(firma).rstrip(b"=").decode("ascii")


def create_jwt(
    payload: dict[str, Any], expires_minutes: int = JWT_EXPIRACION_MINUTOS
) -> str:
    """Crea un JWT firmado con HS256 y reclamaciones estándar.

    Obliga a incluir `sub` (subject) y añade `iat`/`exp` automáticamente.

    Raises:
        ValueError: si falta `sub` en el payload.
        RuntimeError: si JWT_SECRET no está configurado.
    """
    if "sub" not in payload:
        raise ValueError("El payload del JWT debe incluir 'sub'.")

    header = {"alg": JWT_ALGORITMO, "typ": "JWT"}
    now = int(time.time())
    body = {
        **payload,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }

    enc_header = _b64url_encode(header)
    enc_payload = _b64url_encode(body)
    firma = _firmar(enc_header, enc_payload)

    return f"{enc_header}.{enc_payload}.{firma}"


def verify_jwt(token: str) -> dict[str, Any] | None:
    """Verifica firma, algoritmo y expiración del JWT.

    Returns:
        El payload (dict) si el token es válido; None en caso contrario.
        Nunca lanza excepciones ante tokens malformados o alterados.
    """
    if not isinstance(token, str) or not token:
        return None

    try:
        partes = token.split(".")
        if len(partes) != 3:
            return None
        enc_header, enc_payload, enc_sig = partes

        # Validar algoritmo para evitar confusión de algoritmo (alg=none, RS256...)
        header = _b64url_decode(enc_header)
        if not isinstance(header, dict) or header.get("alg") != JWT_ALGORITMO:
            return None

        # Verificar firma en tiempo constante
        firma_esperada = _firmar(enc_header, enc_payload)
        if not hmac.compare_digest(firma_esperada, enc_sig):
            return None

        payload = _b64url_decode(enc_payload)
        if not isinstance(payload, dict):
            return None

        # Validar reclamaciones obligatorias
        for reclamacion in JWT_RECLAMOS_OBLIGATORIOS:
            if reclamacion not in payload:
                return None

        # Validar expiración (debe ser int)
        exp = payload.get("exp")
        if not isinstance(exp, int):
            return None
        if exp < int(time.time()):
            return None

        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError,
            binascii.Error):
        return None
