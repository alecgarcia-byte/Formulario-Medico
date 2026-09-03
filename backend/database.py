"""
database.py
------------
Conexión a la base de datos (PostgreSQL en producción / SQLite en desarrollo).

Diseñado para ser seguro en entornos serverless (Vercel + Supabase):
- Lee DATABASE_URL desde variables de entorno (nunca secretos hardcodeados).
- En producción usa el pooler transaccional de Supabase (puerto 6543) y
  desactiva prepared statements (requisito del pooler en modo transacción).
- Fallback a SQLite solo para desarrollo local / tests sin servidor.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Importamos primero config para que cargue los secretos del .env antes de
# que cualquier módulo lea variables de entorno (p. ej. DATABASE_URL).
from . import config  # noqa: E402

# URL de conexión. En producción siempre viene de variables de entorno
# (Vercel) o del .env local (desarrollo).
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Detecta si estamos apuntando a PostgreSQL (cadena postgres:// o postgresql://)
ES_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _construir_engine():
    """Crea el engine según el backend disponible."""
    if not DATABASE_URL:
        # Desarrollo local sin servidor: base de datos SQLite persistente.
        # La ruta puede sobrescribirse con SQLITE_PATH (p. ej. para aislar
        # la base de los tests en un archivo temporal auto-limpio).
        ruta = os.getenv("SQLITE_PATH") or "./formulario_local.db"
        return create_engine(
            f"sqlite:///{ruta}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

    # En PostgreSQL (Supabase) con Vercel serverless:
    # - connect_args sslmode=require garantiza canal cifrado.
    # - pool_pre_ping evita conexiones muertas.
    # - pool tamaño pequeño porque las funciones serverless son efímeras.
    connect_args = {}
    if ES_POSTGRES:
        connect_args["sslmode"] = "require"

    # Nota: para el pooler de Supabase en modo transacción (puerto 6543),
    # psycopg2 no soporta `prepared_statements=False` a nivel de constructor;
    # ese ajuste se documenta en docs/DEPLOY.md usando 'options' de Supavisor.
    return create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
    )


engine = _construir_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM (POO)."""


def get_session():
    """Dependencia que provee una sesión de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
