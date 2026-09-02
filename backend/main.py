"""
main.py
-------
Aplicación FastAPI del Formulário Médico Acadêmico.

Punto de entrada para desarrollo (uvicorn) y para Vercel serverless.

Endpoints (Fase 4):
- POST /respostas : recibe, valida, cifra y persiste un registro.

Endpoints admin (Fase 6): login, listado, detalle, exportación.
"""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config, export, models, schemas
from .database import Base, engine, get_session
from .utils.auth import admin_autenticado
from .utils.middleware import SeguridadHeadersMiddleware
from .utils.security import (
    CifradoError,
    create_jwt,
    decrypt_field,
    encrypt_field,
    es_password_admin,
)


def _configurar_logging() -> logging.Logger:
    """Configura el logger de la aplicación (StreamHandler)."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger("formulario")
    if not root.handlers:
        root.setLevel(logging.INFO)
        root.addHandler(handler)
    return root


logger = _configurar_logging()

# Creamos las tablas en arranque (apropiado para serverless/lite).
# Para producción con migraciones (Alembic) se elimina/ajusta esta línea.
Base.metadata.create_all(bind=engine)


def _validar_secretos_al_arranque() -> None:
    """Valida la presencia/validez de los secretos al levantar la app.

    Falla rápido si falta un secreto imprescindible (recomendado en
    producción) en lugar de funcionar de forma insegura.
    """
    if not config.ES_PRODUCCION:
        return  # en desarrollo permitimos arrancar y avisar por logs
    config.secret_key_aes()
    config.jwt_secret()
    config.credenciales_admin()


def _crear_aplicacion() -> FastAPI:
    """Factory que construye y configura la aplicación FastAPI."""
    produccion = config.ES_PRODUCCION

    # Arranque seguro: validamos secretos en producción.
    _validar_secretos_al_arranque()

    app = FastAPI(
        title="Formulário Médico Acadêmico API",
        description="API de recolección de datos médicos y académicos de profesores.",
        version="1.0.0",
        # En producción deshabilitamos la documentación interactiva para
        # reducir superficie de exposición. En dev queda disponible.
        docs_url=None if produccion else "/docs",
        redoc_url=None,
    )

    # CORS: solo orígenes permitidos (nunca "*"). Ajustable por variable.
    origenes = ["http://localhost:5500", "http://127.0.0.1:5500"]
    url_front = config.frontend_url()
    if url_front:
        origenes.append(url_front)
    if not produccion:
        origenes.extend(["http://localhost:8000", "http://127.0.0.1:8000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
        max_age=600,
    )

    app.add_middleware(SeguridadHeadersMiddleware)

    # --- Manejo centralizado de errores ---
    @app.exception_handler(HTTPException)
    async def manejar_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def manejar_excepcion_general(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Error no manejado en %s %s",
            request.method,
            request.url.path,
        )
        # No exponemos detalles internos del error al cliente.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor."},
        )

    # --- Endpoint: recibir formulario ---
    @app.post(
        "/api/respostas",
        response_model=schemas.RespuestaCreada,
        status_code=status.HTTP_201_CREATED,
    )
    def crear_resposta(
        payload: schemas.ProfesorIn,
        request: Request,
        db: Session = Depends(get_session),
    ) -> schemas.RespuestaCreada:
        """Valida, cifra campos sensibles y persiste el registro."""
        try:
            registro = models.Profesor(
                nombre=payload.nombre,
                apellido=payload.apellido,
                fecha_nacimiento=payload.fecha_nacimiento,
                sexo=payload.sexo,
                nacionalidad=payload.nacionalidad,
                documento_enc=encrypt_field(payload.documento),
                fiscal_enc=encrypt_field(payload.fiscal),
                telefono=payload.telefono,
                correo_personal=str(payload.correo_personal),
                correo_institucional=str(payload.correo_institucional),
                titulo_grado=payload.titulo_grado,
                universidad=payload.universidad,
                ano_graduacion=payload.ano_graduacion,
                titulo_especialidad=payload.titulo_especialidad,
                ano_especialidad=payload.ano_especialidad,
                subespecialidad=payload.subespecialidad,
                grado_academico=payload.grado_academico,
                registro_profesional=payload.registro_profesional,
                anos_experiencia_docente=payload.anos_experiencia_docente,
                anos_experiencia_assistencial=payload.anos_experiencia_assistencial,
                cargo_docente=payload.cargo_docente,
                institucion=payload.institucion,
                departamento=payload.departamento,
            )
            db.add(registro)
            db.commit()
            db.refresh(registro)
            logger.info(
                "Resposta criada id=%s ip=%s", registro.id,
                request.client.host if request.client else "unknown",
            )
            return schemas.RespuestaCreada(success=True, id=registro.id)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001 - error de persistencia
            db.rollback()
            logger.exception("Erro ao persistir resposta")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível salvar os dados. Tente novamente.",
            ) from exc

    # --- Ruta de chequeo de salud ---
    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "formulario-api"}

    # ==================================================================
    # Panel admin (protegido por JWT)
    # ==================================================================

    @app.post("/api/admin/login", response_model=schemas.TokenRespuesta)
    def admin_login(
        credenciales: schemas.LoginIn,
        request: Request,
    ) -> schemas.TokenRespuesta:
        """Autentica al administrador y devuelve un JWT."""
        if not es_password_admin(credenciales.usuario, credenciales.password):
            logger.warning(
                "Login admin fallido ip=%s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_jwt({"sub": "admin"})
        logger.info("Login admin OK ip=%s",
                    request.client.host if request.client else "unknown")
        return schemas.TokenRespuesta(access_token=token)

    @app.get("/api/admin/respostas", response_model=schemas.RespostasPagina)
    def listar_respostas(
        request: Request,
        pagina: int = 1,
        tamano: int = 50,
        cargo: str | None = None,
        universidad: str | None = None,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_autenticado),
    ) -> schemas.RespostasPagina:
        """Lista paginada de registros, con campos sensibles descifrados."""
        # Límites de seguridad sobre los parámetros de paginación.
        pagina = max(1, pagina)
        tamano = min(max(1, tamano), 100)

        # Construcción declarativa de la consulta (SQLAlchemy -> sin SQLi).
        consulta = select(models.Profesor)
        if cargo:
            consulta = consulta.where(models.Profesor.cargo_docente == cargo)
        if universidad:
            consulta = consulta.where(models.Profesor.universidad.ilike(
                f"%{universidad}%"
            ))

        total = db.scalar(
            select(func.count()).select_from(
                consulta.order_by(None).subquery()
            )
        ) or 0

        registros = (
            db.scalars(
                consulta.order_by(models.Profesor.created_at.desc())
                .offset((pagina - 1) * tamano)
                .limit(tamano)
            ).all()
        )

        items = [_a_item_con_descifrado(r) for r in registros]
        return schemas.RespostasPagina(
            total=total, pagina=pagina, tamano=tamano, items=items
        )

    @app.get("/api/admin/respostas/{resposta_id}", response_model=schemas.RespostaItem)
    def detalle_resposta(
        resposta_id: str,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_autenticado),
    ) -> schemas.RespostaItem:
        """Detalle de un registro con campos sensibles descifrados."""
        registro = db.get(models.Profesor, resposta_id)
        if registro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro não encontrado.",
            )
        return _a_item_con_descifrado(registro)

    @app.get("/api/admin/exportar")
    def exportar_respostas(
        request: Request,
        cargo: str | None = None,
        universidad: str | None = None,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_autenticado),
    ) -> StreamingResponse:
        """Genera y descarga un .xlsx con los registros (descifrados)."""
        consulta = select(models.Profesor)
        if cargo:
            consulta = consulta.where(models.Profesor.cargo_docente == cargo)
        if universidad:
            consulta = consulta.where(models.Profesor.universidad.ilike(
                f"%{universidad}%"
            ))
        registros = db.scalars(
            consulta.order_by(models.Profesor.created_at.desc())
        ).all()

        try:
            contenido, nombre = export.generar_excel(registros)
        except CifradoError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível gerar a exportação.",
            ) from exc

        logger.info(
            "Exportação gerada por admin (registros=%d) ip=%s",
            len(registros),
            request.client.host if request.client else "unknown",
        )
        return StreamingResponse(
            iter([contenido]),
            media_type=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{nombre}"'
            },
        )

    return app


def _a_item_con_descifrado(reg: models.Profesor) -> schemas.RespostaItem:
    """Convierte un registro a detalle admin descifrando campos sensibles.

    El descifrado se hace SOLO en endpoints autenticados (panel admin).
        Si un campo no puede descifrarse, se devuelve un marcador en lugar de
        descartar todo el registro.
    """
    def _des(enc: str) -> str:
        try:
            return decrypt_field(enc)
        except CifradoError:
            return "[indisponível]"

    return schemas.RespostaItem(
        id=reg.id,
        nombre=reg.nombre,
        apellido=reg.apellido,
        fecha_nacimiento=reg.fecha_nacimiento,
        sexo=reg.sexo,
        nacionalidad=reg.nacionalidad,
        documento=_des(reg.documento_enc),
        fiscal=_des(reg.fiscal_enc),
        telefono=reg.telefono,
        correo_personal=reg.correo_personal,
        correo_institucional=reg.correo_institucional,
        titulo_grado=reg.titulo_grado,
        universidad=reg.universidad,
        ano_graduacion=reg.ano_graduacion,
        titulo_especialidad=reg.titulo_especialidad,
        ano_especialidad=reg.ano_especialidad,
        subespecialidad=reg.subespecialidad,
        grado_academico=reg.grado_academico,
        registro_profesional=reg.registro_profesional,
        anos_experiencia_docente=reg.anos_experiencia_docente,
        anos_experiencia_assistencial=reg.anos_experiencia_assistencial,
        cargo_docente=reg.cargo_docente,
        institucion=reg.institucion,
        departamento=reg.departamento,
        created_at=reg.created_at,
    )


app = _crear_aplicacion()
