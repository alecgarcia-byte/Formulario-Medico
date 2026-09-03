"""
conftest.py
-----------
Fixtures compartidas de pytest para el backend.

Antes de importar `backend.main` se configuran variables de entorno (clave
AES, secreto JWT, token admin) con valores seguros de prueba y una
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

# Aislamos la DB de los tests en un archivo temporal y único; se elimina
# automáticamente al final de la sesión. Así no dejamos `formulario_local.db`
# ni datos de prueba en la raíz del proyecto.
import tempfile  # noqa: E402

_DB_TEMP = tempfile.NamedTemporaryFile(
    suffix=".db", prefix="tests_formulario_", delete=False
)
os.environ.setdefault("SQLITE_PATH", _DB_TEMP.name)
_DB_TEMP.close()

os.environ.setdefault(
    "SECRET_KEY_AES", base64.b64encode(b"k" * 32).decode("ascii")
)
os.environ.setdefault("JWT_SECRET", "clave-de-test-" + "x" * 30)

# Token/llave de acceso al panel admin (URL secreta). Mín. 20 caracteres.
# Debe coincidir con la constante TOKEN de test_admin.py.
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token-12345678901234567890")

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
def client():
    """TestClient con la app real; cada petición usa una sesión de BD limpia."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


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


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Elimina la BD SQLite temporal de los tests al finalizar la sesión."""
    # Liberamos el pool de conexiones para que Windows no bloquee el archivo.
    try:
        engine.dispose()
    except Exception:  # noqa: BLE001
        pass
    ruta = os.environ.get("SQLITE_PATH")
    if ruta and os.path.exists(ruta):
        try:
            os.remove(ruta)
        except OSError:
            pass
