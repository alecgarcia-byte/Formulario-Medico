"""
schemas.py
----------
Esquemas Pydantic (POO) para validación de entrada y serialización de salida.

Los validadores replican y endurecen las reglas del frontend: límites de
longitud mín/máx, patrones whitelist (anti-inyección), tipos por campo y
enums. Esta es la defensa principal en el servidor.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# Enums permitidos (alineados con el frontend)
Sexo = Literal["Masculino", "Feminino", "Outro"]
GradoAcademico = Literal["Graduado", "Especialista", "Mestre", "Doutor", "Pós-doutor"]
CargoDocente = Literal["Titular", "Associado", "Assistente", "Convidado"]

# Patrones whitelist (rechaza caracteres de inyección)
# 're' nativo no soporta \p{L}; validamos los caracteres permitidos de
# forma programática con str.isalpha() (letras Unicode) o isalnum().
_PATRON_ALFANUM = re.compile(r"^[A-Za-z0-9\s\.\-]+$")
_PATRON_NUM = re.compile(r"^[0-9]+$")
_PATRON_TEL = re.compile(r"^\+?[0-9\s\-\(\)\.]+$")

# Caracteres adicionales permitidos además de letras/espacios
_EXTRA_LETRAS = set("'.- ")


def _rechaza_control(texto: str) -> bool:
    """True si el texto contiene caracteres de control (CR/LF/NUL/ESC...).

    Previene inyección de CRLF y otros bytes de control que podrían alterar
    logs, respuestas o exportaciones, incluso si pasan los checks de letra.
    """
    return any(ord(ch) < 32 or ord(ch) == 127 for ch in texto)


def _es_solo_letras(texto: str, extra: str = "") -> bool:
    """True si todos los caracteres son letras Unicode, espacios o los extras."""
    permitidos = _EXTRA_LETRAS | set(extra)
    return (
        bool(texto)
        and not _rechaza_control(texto)
        and all(
            ch.isalpha() or ch.isspace() or ch in permitidos for ch in texto
        )
    )


def _es_solo_letras_digitos(texto: str) -> bool:
    """True si el texto usa solo letras Unicode, dígitos y separadores simples."""
    return (
        bool(texto)
        and not _rechaza_control(texto)
        and all(ch.isalnum() or ch in " .-" for ch in texto)
    )

_MAX_GLOBAL = 120


class ProfesorIn(BaseModel):
    """Datos de entrada del formulario (validación estricta)."""

    nombre: str = Field(min_length=2, max_length=80)
    apellido: str = Field(min_length=2, max_length=80)
    fecha_nacimiento: date
    sexo: Sexo
    nacionalidad: str = Field(min_length=2, max_length=60)
    documento: str = Field(min_length=4, max_length=20)
    fiscal: str = Field(min_length=3, max_length=15)
    telefono: str = Field(min_length=8, max_length=20)
    correo_personal: EmailStr
    correo_institucional: EmailStr

    titulo_grado: str = Field(min_length=2, max_length=100)
    universidad: str = Field(min_length=2, max_length=100)
    ano_graduacion: int = Field(ge=1900, le=2100)
    titulo_especialidad: str = Field(min_length=2, max_length=100)
    ano_especialidad: int = Field(ge=1900, le=2100)
    subespecialidad: str | None = Field(None, max_length=100)
    grado_academico: GradoAcademico
    registro_profesional: str = Field(min_length=3, max_length=20)
    anos_experiencia_docente: int = Field(ge=0, le=80)
    anos_experiencia_assistencial: int = Field(ge=0, le=80)

    cargo_docente: CargoDocente
    institucion: str | None = Field(None, max_length=100)
    departamento: str | None = Field(None, max_length=100)

    # Consentimiento (obligatorio: debe ser True)
    consentimiento: bool = True

    model_config = ConfigDict(str_strip_whitespace=True)

    # --- Validadores de patrón (anti-inyección) ---
    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombre(cls, v: str) -> str:
        if not _es_solo_letras(v):
            raise ValueError("Nombre/Sobrenome com caracteres inválidos.")
        return v

    @field_validator("nacionalidad")
    @classmethod
    def _validar_nacionalidad(cls, v: str) -> str:
        if not _es_solo_letras(v):
            raise ValueError("Nacionalidade com caracteres inválidos.")
        return v

    @field_validator("documento")
    @classmethod
    def _validar_documento(cls, v: str) -> str:
        if not _PATRON_ALFANUM.match(v):
            raise ValueError("Documento com caracteres inválidos.")
        return v

    @field_validator("fiscal")
    @classmethod
    def _validar_fiscal(cls, v: str) -> str:
        if not _PATRON_NUM.match(v):
            raise ValueError("NIF deve conter somente números.")
        return v

    @field_validator("telefono")
    @classmethod
    def _validar_telefono(cls, v: str) -> str:
        if not _PATRON_TEL.match(v):
            raise ValueError("Telefone com formato inválido.")
        return v

    @field_validator("titulo_grado", "titulo_especialidad")
    @classmethod
    def _validar_titulos(cls, v: str) -> str:
        if not _es_solo_letras(v, extra="()./-"):
            raise ValueError("Título com caracteres inválidos.")
        return v

    @field_validator("universidad")
    @classmethod
    def _validar_universidad(cls, v: str) -> str:
        if not _es_solo_letras(v, extra="()./-&"):
            raise ValueError("Universidade com caracteres inválidos.")
        return v

    @field_validator("subespecialidad", "institucion", "departamento")
    @classmethod
    def _validar_opcionales(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) > 100:
            raise ValueError("Texto muito longo (máx. 100 caracteres).")
        if not _es_solo_letras(v, extra="()./-&"):
            raise ValueError("Campo opcional com caracteres inválidos.")
        return v

    @field_validator("registro_profesional")
    @classmethod
    def _validar_registro(cls, v: str) -> str:
        if not _es_solo_letras_digitos(v):
            raise ValueError(
                "Registro Profissional com caracteres inválidos."
            )
        return v

    @field_validator("consentimiento")
    @classmethod
    def _validar_consentimiento(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Consentimento informado é obrigatório.")
        return v

    @field_validator("fecha_nacimiento")
    @classmethod
    def _validar_fecha(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Data de nascimento não pode ser futura.")
        if v.year < 1900:
            raise ValueError("Data de nascimento inválida.")
        return v

    @model_validator(mode="after")
    def _validar_coherencia(self) -> "ProfesorIn":
        """Valida la coherencia temporal entre fechas y años académicos."""
        # El año de graduación debe ser posterior (o igual) al de nacimiento.
        if self.fecha_nacimiento and self.ano_graduacion < self.fecha_nacimiento.year:
            raise ValueError(
                "Ano de graduação anterior ao ano de nascimento."
            )
        # La especialidad no puede preceder a la graduación.
        if self.ano_especialidad < self.ano_graduacion:
            raise ValueError(
                "Ano de especialidade anterior ao ano de graduação."
            )
        return self


class ProfesorOut(BaseModel):
    """Salida pública de un registro (sin exponer cifrado crudo)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    apellido: str
    fecha_nacimiento: date
    sexo: str
    nacionalidad: str
    telefono: str
    correo_personal: EmailStr
    correo_institucional: EmailStr
    titulo_grado: str
    universidad: str
    ano_graduacion: int
    titulo_especialidad: str
    ano_especialidad: int
    subespecialidad: str | None
    grado_academico: str
    registro_profesional: str
    anos_experiencia_docente: int
    anos_experiencia_assistencial: int
    cargo_docente: str
    institucion: str | None
    departamento: str | None
    created_at: datetime


class RespuestaCreada(BaseModel):
    """Respuesta del POST /respostas (no expone datos sensibles)."""

    success: bool
    id: uuid.UUID


class TokenRespuesta(BaseModel):
    """Respuesta del login admin."""

    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    """Credenciales de login del admin."""

    usuario: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)

    model_config = ConfigDict(str_strip_whitespace=True)


class RespostaItem(ProfesorOut):
    """Detalle de un registro, con campos sensibles descifrados."""

    documento: str
    fiscal: str


class RespostasPagina(BaseModel):
    """Respuesta paginada del listado admin."""

    total: int
    pagina: int
    tamano: int
    items: list[RespostaItem]
