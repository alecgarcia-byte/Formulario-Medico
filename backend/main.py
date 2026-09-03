"""
main.py
-------
Aplicación FastAPI del Formulário Médico Acadêmico.

Punto de entrada para desarrollo (uvicorn) y para Vercel serverless.

Endpoints (Fase 4):
- POST /respostas : recibe, valida, cifra y persiste un registro.

Endpoints admin (acceso por URL secreta ADMIN_TOKEN):
- GET /admin-{token}                          : sirve el panel (HTML), solo si token válido.
- GET /api/admin/{token}/respostas            : listado paginado (descifra campos sensibles).
- GET /api/admin/{token}/respostas/{id}       : detalle de un registro.
- GET /api/admin/{token}/exportar             : exporta a Excel (.xlsx).
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config, export, models, schemas
from .database import Base, engine, get_session
from .utils.auth import admin_token_verificado
from .utils.middleware import SeguridadHeadersMiddleware
from .utils.security import CifradoError, decrypt_field, encrypt_field


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
    config.admin_token()  # URL/secreta de acceso al panel admin


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
    # Panel admin (protegido por URL/llave secreta ADMIN_TOKEN)
    # ==================================================================

    @app.get("/admin-{token}", response_class=HTMLResponse)
    def panel_admin_html(
        request: Request,
        token: str,
    ) -> HTMLResponse:
        """Sirve el panel admin (sin login) SOLO si el token es correcto.

        Devuelve el HTML del panel con el token embebido en el navegador
        para que el JS pueda llamar a la API admin. Si el token no coincide,
        se devuelve 404 para no revelar la existencia del panel.
        """
        try:
            payload = admin_token_verificado(token)
        except HTTPException:
            raise
        del payload
        try:
            html = _leer_panel_admin()
        except OSError as exc:
            logger.exception("No se pudo leer el panel admin")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            ) from exc
        # Inyectamos el token (el CIERTO, no el de la ruta) por seguridad.
        html = html.replace("__ADMIN_TOKEN__", config.admin_token())
        return HTMLResponse(html)

    @app.get("/api/admin/{token}/respostas", response_model=schemas.RespostasPagina)
    def listar_respostas(
        request: Request,
        token: str,
        pagina: int = 1,
        tamano: int = 50,
        cargo: str | None = None,
        universidad: str | None = None,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_token_verificado),
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

    @app.get("/api/admin/{token}/respostas/{resposta_id}", response_model=schemas.RespostaItem)
    def detalle_resposta(
        resposta_id: str,
        token: str,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_token_verificado),
    ) -> schemas.RespostaItem:
        """Detalle de un registro con campos sensibles descifrados."""
        registro = db.get(models.Profesor, resposta_id)
        if registro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro não encontrado.",
            )
        return _a_item_con_descifrado(registro)

    @app.get("/api/admin/{token}/exportar")
    def exportar_respostas(
        request: Request,
        token: str,
        cargo: str | None = None,
        universidad: str | None = None,
        db: Session = Depends(get_session),
        _admin: dict = Depends(admin_token_verificado),
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


def _leer_panel_admin() -> str:
    """Lee el HTML del panel admin (plantilla) desde la raíz del proyecto.

    El archivo contiene el marcador `__ADMIN_TOKEN__` que el endpoint
    `panel_admin_html` reemplaza con el token real antes de servirlo.
    """
    raiz = Path(__file__).resolve().parent.parent
    ruta = raiz / "porphyria" / "panel_admin.html"
    return ruta.read_text(encoding="utf-8")


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
