"""
test_seguridad.py
------------------
Pruebas unitarias de utils/security.py: cifrado AES-256-GCM y JWT.
"""

from __future__ import annotations

import base64

import pytest

from backend.utils.security import (
    CifradoError,
    create_jwt,
    decrypt_field,
    encrypt_field,
    verify_jwt,
)


# ============================ AES-256-GCM ===============================


class TestCifrado:
    def test_roundtrip(self):
        cifrado = encrypt_field("AB1234567")
        assert decrypt_field(cifrado) == "AB1234567"

    def test_nonce_unico(self):
        a = encrypt_field("dato-repetido")
        b = encrypt_field("dato-repetido")
        assert a != b  # mismo texto -> distinto ciphertext (nonce único)

    def test_dato_alterado_rechazado(self):
        cifrado = encrypt_field("secreto")
        # Corrompemos el último carácter del base64 manteniendo longitud.
        corrupto = cifrado[:-1] + ("A" if cifrado[-1] != "A" else "B")
        with pytest.raises(CifradoError):
            decrypt_field(corrupto)

    def test_formato_corrupto_rechazado(self):
        with pytest.raises(CifradoError):
            decrypt_field("no-es-base64-valido!!")

    def test_vacio_rechazado(self):
        with pytest.raises(CifradoError):
            encrypt_field("")


# ================================ JWT ====================================


class TestJWT:
    def test_crear_y_verificar(self):
        token = create_jwt({"sub": "admin"})
        payload = verify_jwt(token)
        assert payload is not None
        assert payload["sub"] == "admin"

    def test_token_manipulado_rechazado(self):
        token = create_jwt({"sub": "admin"})
        partes = token.split(".")
        partes[2] = "firma-falsa" + "x"
        assert verify_jwt(".".join(partes)) is None

    def test_ataque_alg_none(self):
        # Header {alg:none} + payload firmado con nada -> debe rechazarse.
        import hmac
        import json

        def b64url(obj):
            raw = json.dumps(obj, separators=(",", ":")).encode()
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        header = b64url({"alg": "none", "typ": "JWT"})
        payload = b64url({"sub": "admin", "iat": 0, "exp": 9999999999})
        token = f"{header}.{payload}."
        assert verify_jwt(token) is None

    def test_payload_sin_sub_rechazado(self):
        with pytest.raises(ValueError):
            create_jwt({"rol": "admin"})
