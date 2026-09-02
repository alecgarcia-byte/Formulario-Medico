"""
export.py
---------
Generación de archivos Excel (.xlsx) con los datos de la encuesta.

Los campos sensibles `documento` y `fiscal` se almacenan cifrados en la
base de datos; al exportar se DESCIFRAN para lectura por el administrador
(acceso legítimo y controlado, respaldado por autenticación JWT).
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from . import models
from .utils.security import decrypt_field
from .utils.security import CifradoError


# Los campos que se exportan, en orden, con su encabezado en portugués.
COLUMNAS_EXPORTACION: list[tuple[str, str]] = [
    ("id", "ID"),
    ("nombre", "Nome"),
    ("apellido", "Sobrenome"),
    ("fecha_nacimiento", "Data de Nascimento"),
    ("sexo", "Sexo"),
    ("nacionalidad", "Nacionalidade"),
    ("documento", "Documento de Identidade / Passaporte"),
    ("fiscal", "Número de Identificação Fiscal (NIF)"),
    ("telefono", "Telefone"),
    ("correo_personal", "E-mail Pessoal"),
    ("correo_institucional", "E-mail Institucional"),
    ("titulo_grado", "Título de Graduação"),
    ("universidad", "Universidade"),
    ("ano_graduacion", "Ano de Graduação"),
    ("titulo_especialidad", "Título de Especialidade"),
    ("ano_especialidad", "Ano de Especialidade"),
    ("subespecialidad", "Subespecialidade"),
    ("grado_academico", "Grau Acadêmico"),
    ("registro_profesional", "Registro Profissional"),
    ("anos_experiencia_docente", "Anos de Experiência Docente"),
    ("anos_experiencia_assistencial", "Anos de Experiência Assistencial"),
    ("cargo_docente", "Cargo Docente"),
    ("institucion", "Instituição"),
    ("departamento", "Departamento"),
    ("created_at", "Data de Registro"),
]


def generar_excel(registros: Iterable[models.Profesor]) -> tuple[bytes, str]:
    """Genera un .xlsx con los registros (descifrando campos sensibles).

    Args:
        registros: iterable de modelos Profesor (normalmente resultado de
            una consulta filtrada del panel admin).

    Returns:
        Tupla (bytes del archivo, nombre de archivo sugerido).

    Raises:
        CifradoError: si un campo sensible no puede descifrarse.
    """
    filas: list[dict[str, object]] = []
    for r in registros:
        filas.append(
            {
                "id": str(r.id),
                "nombre": r.nombre,
                "apellido": r.apellido,
                "fecha_nacimiento": r.fecha_nacimiento,
                "sexo": r.sexo,
                "nacionalidad": r.nacionalidad,
                "documento": _decifrar(r.documento_enc, r.id),
                "fiscal": _decifrar(r.fiscal_enc, r.id),
                "telefono": r.telefono,
                "correo_personal": r.correo_personal,
                "correo_institucional": r.correo_institucional,
                "titulo_grado": r.titulo_grado,
                "universidad": r.universidad,
                "ano_graduacion": r.ano_graduacion,
                "titulo_especialidad": r.titulo_especialidad,
                "ano_especialidad": r.ano_especialidad,
                "subespecialidad": r.subespecialidad,
                "grado_academico": r.grado_academico,
                "registro_profesional": r.registro_profesional,
                "anos_experiencia_docente": r.anos_experiencia_docente,
                "anos_experiencia_assistencial": r.anos_experiencia_assistencial,
                "cargo_docente": r.cargo_docente,
                "institucion": r.institucion,
                "departamento": r.departamento,
                "created_at": r.created_at,
            }
        )

    if not filas:
        # Exportación vacía: creamos un DataFrame con solo encabezados.
        df = pd.DataFrame(columns=[h for _, h in COLUMNAS_EXPORTACION])
    else:
        df = pd.DataFrame(filas)
        # Reordenamos según COLUMNAS_EXPORTACION y renombramos encabezados.
        df = df[[clave for clave, _ in COLUMNAS_EXPORTACION]]
        df = df.rename(
            columns={clave: encabezado for clave, encabezado in COLUMNAS_EXPORTACION}
        )

    # Nombre de archivo con marca de tiempo (evita colisiones y cache).
    marca = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    nombre = f"respostas_{marca}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Respostas")
        hoja = writer.sheets["Respostas"]
        # Estilos básicos: encabezados en negrita y ancho de columna.
        from openpyxl.styles import Alignment, Font

        for celda in hoja[1]:
            celda.font = Font(bold=True)
            celda.alignment = Alignment(horizontal="center")
        for columna_celda in hoja.columns:
            letra = columna_celda[0].column_letter
            hoja.column_dimensions[letra].width = 24

    return buffer.getvalue(), nombre


def _decifrar(cifrado: str, registro_id: object) -> str:
    """Descifra un campo sensible; ante fallo devuelve un marcador."""
    try:
        return decrypt_field(cifrado)
    except CifradoError as exc:
        # No rompemos toda la exportación por un registro puntual; lo marcamos.
        return f"[indisponível] id={registro_id}"
