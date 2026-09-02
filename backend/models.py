"""
models.py
---------
Modelo ORM (SQLAlchemy, enfoque POO) de la tabla `professores`.

Los campos sensibles `documento` y `fiscal` se almacenan CIFRADOS
(columna `documento_enc` / `fiscal_enc`). El cifrado se realiza en la capa
de servicios antes de la persistencia (ver utils/security.py y main.py).

Los nombres de las columnas siguen la convención del proyecto (español);
los valores visibles al usuario final están en portugués.
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    CHAR,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UUIDChar(TypeDecorator):
    """Tipo portable de UUID: nativo en PostgreSQL, CHAR(36) en SQLite."""

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value if dialect.name == "postgresql" else str(value)

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def _utcnow() -> datetime:
    """Timestamp UTC con zona horaria."""
    return datetime.now(timezone.utc)


class Profesor(Base):
    """Registro de un profesor participante del formulario."""

    __tablename__ = "professores"
    __table_args__ = (
        Index("ix_professores_correo_institucional", "correo_institucional"),
        Index("ix_professores_registro_profesional", "registro_profesional"),
        Index("ix_professores_created_at", "created_at"),
    )

    # --- Identificador ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUIDChar, primary_key=True, default=uuid.uuid4
    )

    # --- Datos personales ---
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[str] = mapped_column(String(20), nullable=False)
    nacionalidad: Mapped[str] = mapped_column(String(60), nullable=False)

    # Campos sensibles -> cifrados
    documento_enc: Mapped[str] = mapped_column(Text, nullable=False)
    fiscal_enc: Mapped[str] = mapped_column(Text, nullable=False)

    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    correo_personal: Mapped[str] = mapped_column(String(254), nullable=False)
    correo_institucional: Mapped[str] = mapped_column(
        String(254), nullable=False
    )

    # --- Formación académica y profesional ---
    titulo_grado: Mapped[str] = mapped_column(String(100), nullable=False)
    universidad: Mapped[str] = mapped_column(String(100), nullable=False)
    ano_graduacion: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo_especialidad: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    ano_especialidad: Mapped[int] = mapped_column(Integer, nullable=False)
    subespecialidad: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    grado_academico: Mapped[str] = mapped_column(String(30), nullable=False)
    registro_profesional: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    anos_experiencia_docente: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    anos_experiencia_assistencial: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    # --- Datos laborales e institucionales ---
    cargo_docente: Mapped[str] = mapped_column(String(30), nullable=False)
    institucion: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    departamento: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # --- Auditoría ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
