"""
conftest.py
-----------
Fixtures compartidas de pytest para el backend.

Antes de importar `backend.main` se configuran variables de entorno (clave
AES, secreto JWT, credenciales admin) con valores seguros de prueba y una
base SQLite en memoria para aislar los tests.
"""

from __future__ import annotations

import base64
import os
import sys
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

# --- Configuración de entorno ANTES de importar el backend ---
# DATABASE_URL vacío -> backend usa SQLite (misma ruta que dev local),
# con check_same_thread=False, compatible con TestClient.
os.environ.setdefault("DATABASE_URL", "")

# Limpiamos la base SQLite por defecto para empezar cada sesión de tests
# con datos frescos.
_DB_DEFECTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "formulario_local.db",
)
if os.path.exists(_DB_DEFECTO):
    os.remove(_DB_DEFECTO)

os.environ.setdefault(
    "SECRET_KEY_AES", base64.b64encode(b"k" * 32).decode("ascii")
)
os.environ.setdefault("JWT_SECRET", "clave-de-test-" + "x" * 30)
os.environ.setdefault("ADMIN_USER", "admin")

# Generamos un hash bcrypt de prueba (coste bajo para acelerar los tests).
_pass_admin = "super-secreto"
import bcrypt  # noqa: E402

_hash_admin = bcrypt.hashpw(
    _pass_admin.encode("utf-8"), bcrypt.gensalt(rounds=4)
).decode("ascii")
os.environ.setdefault("ADMIN_PASSWORD_HASH", _hash_admin)

# Permitimos importar el paquete backend desde la raíz del proyecto.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROYECTO = os.path.dirname(_ROOT)
if _PROYECTO not in sys.path:
    sys.path.insert(0, _PROYECTO)

from backend.database import Base, engine, get_session  # noqa: E402
from backend.main import app  # noqa: E402

# Creamos las tablas sobre la BD en memoria.
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def password_admin() -> str:
    """Contraseña de admin configurada para los tests."""
    return _pass_admin


@pytest.fixture(scope="session")
def client():
    """TestClient con la app real; cada petición usa una sesión de BD limpia."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def cliente_autenticado(client):
    """TestClient + token JWT de admin listo para usar."""
    token = client.post(
        "/api/admin/login",
        json={"usuario": "admin", "password": _pass_admin},
    ).json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


# --- Datos de ejemplo de un profesor válido ---


@pytest.fixture
def payload_valido() -> dict:
    """Payload válido mínimo para POST /api/respostas."""
    return {
        "nombre": "Ana",
        "apellido": "Souza",
        "fecha_nacimiento": "1990-04-20",
        "sexo": "Feminino",
        "nacionalidad": "Brasileira",
        "documento": "RG1234567",
        "fiscal": "123456789",
        "telefono": "+55 11 99888 7766",
        "correo_personal": "ana.souza@exemplo.com",
        "correo_institucional": "ana.souza@universidade.edu",
        "titulo_grado": "Medicina",
        "universidad": "Universidade de São Paulo",
        "ano_graduacion": 2012,
        "titulo_especialidad": "Cardiologia",
        "ano_especialidad": 2015,
        "subespecialidad": "Hemodinâmica",
        "grado_academico": "Mestre",
        "registro_profesional": "CRM 98765",
        "anos_experiencia_docente": 6,
        "anos_experiencia_assistencial": 9,
        "cargo_docente": "Assistente",
        "institucion": "Hospital Central",
        "departamento": "Cardiologia",
        "consentimiento": True,
    }
