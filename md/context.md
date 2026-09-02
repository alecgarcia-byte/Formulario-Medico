--- context.md ---
# Proyecto: Formulario Médico Académico (Doctorado)

## 1. Resumen y objetivo
**Objetivo principal:** Entregar un sistema web completo (frontend + backend + base de datos + panel admin + exportación a Excel) para la recolección, almacenamiento seguro y análisis de datos médicos y académicos de profesores por especialidad.  
**Alcance:** formulario en portugués para participantes; atributos técnicos (ids, names, clases) en español; backend en Python (FastAPI) desplegado en Vercel; base de datos PostgreSQL (Railway/Neon); repositorio privado en GitHub; exportación a Excel (.xlsx) con Pandas/OpenPyXL; seguridad avanzada (SQLi, XSS, DDoS, cifrado AES-256, security headers).  
**Entregables:** código fuente (frontend y backend), scripts de despliegue, documentación técnica, tests básicos, guía de operación y runbook.

---

## 2. Requisitos funcionales y no funcionales
### Requisitos funcionales (detallados)
- **Formulario único** dividido en secciones:
  - **Dados pessoais:** nombre, apellido, fecha de nacimiento, sexo, nacionalidad, documento/passaporte, NIF, teléfono, correo personal, correo institucional.
  - **Formação acadêmica e profissional:** título de grado, universidad, año de graduación, título de especialidad, año de especialidad, subespecialidad, grado académico, registro profesional, años experiencia docente, años experiencia asistencial.
  - **Dados laborais e institucionais:** cargo docente (titular/associado/assistente/convidado), institución (opcional), departamento (opcional).
- **Validaciones** en cliente (JS) y servidor (Pydantic).
- **Almacenamiento** seguro en PostgreSQL.
- **Panel admin** autenticado (JWT) para listar, filtrar y exportar registros.
- **Exportación** a Excel (.xlsx) con formato legible y encabezados en portugués.
- **Auditoría mínima:** timestamps de creación/actualización, usuario admin que exportó.

### Requisitos no funcionales
- **Interfaz:** portugués (BR) para usuarios; IDs/nombres/clases en español para desarrolladores.
- **Responsividad:** móvil, tablet y desktop.
- **Accesibilidad básica:** labels, focus visible, contraste suficiente.
- **Seguridad:** mitigación contra SQLi, XSS, DDoS; cifrado de campos sensibles; security headers.
- **Observabilidad:** logs estructurados, métricas básicas, alertas por errores críticos.
- **CI/CD:** GitHub Actions + Vercel deploy automático.
- **Privacidad:** cumplimiento con políticas locales y comité de ética; consentimiento informado antes de enviar.

---

## 3. Arquitectura y stack técnico
### Componentes
- **Frontend:** HTML5 semántico + TailwindCSS + CSS custom (`style.css`) + Vanilla JS POO (`app.js`).
- **Backend:** Python 3.10+ con FastAPI; Uvicorn para desarrollo; funciones serverless en Vercel para producción.
- **DB:** PostgreSQL (Railway/Neon). ORM: SQLAlchemy; migraciones con Alembic (opcional).
- **Exportación:** Pandas + OpenPyXL.
- **CI/CD / Hosting:** GitHub (privado) + Vercel (frontend y backend). Variables de entorno en Vercel.
- **Seguridad adicional:** cryptography (AES-256-GCM), bcrypt para contraseñas admin, python-dotenv para local dev.

### Endpoints API (resumen)
- `POST /respostas` → recibir y validar formulario; cifrar campos sensibles; guardar en DB; devolver `{ success: true, id }`.
- `GET /admin/respostas` → listado paginado (autenticado).
- `GET /admin/respostas/{id}` → detalle de registro (autenticado; descifra campos sensibles si corresponde).
- `GET /admin/exportar` → genera y devuelve `.xlsx` (autenticado).
- `POST /admin/login` → autenticación admin (devuelve JWT).

---

## 4. Modelo de datos (esquema resumido)
**Tabla: professores**
- `id` UUID PK
- `nombre` VARCHAR
- `apellido` VARCHAR
- `fecha_nacimiento` DATE
- `sexo` VARCHAR (enum)
- `nacionalidad` VARCHAR
- `documento_enc` TEXT (AES-256 cifrado)
- `fiscal_enc` TEXT (AES-256 cifrado)
- `telefono` VARCHAR
- `correo_personal` VARCHAR
- `correo_institucional` VARCHAR
- `titulo_grado` VARCHAR
- `universidad` VARCHAR
- `ano_graduacion` INT
- `titulo_especialidad` VARCHAR
- `ano_especialidad` INT
- `subespecialidad` VARCHAR NULLABLE
- `grado_academico` VARCHAR
- `registro_profesional` VARCHAR
- `anos_experiencia_docente` INT
- `anos_experiencia_assistencial` INT
- `cargo_docente` VARCHAR (enum)
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

**Índices recomendados:** `correo_institucional`, `registro_profesional`, `created_at`.

---

## 5. Seguridad técnica (implementación práctica)
### Cifrado de datos sensibles
- **Algoritmo:** AES-256-GCM.
- **Clave:** `SECRET_KEY_AES` en variables de entorno (Vercel/GitHub Secrets).
- **Rotación:** documentar procedimiento; mantener versión de clave en DB si se implementa rotación (key_id).
- **Librería:** `cryptography` (Fernet no recomendado para este caso; usar AES-GCM con IV/nonce).

### Prevención SQLi
- Usar SQLAlchemy con parámetros enlazados.
- Nunca concatenar SQL con valores del usuario.

### Prevención XSS
- Sanitizar entradas en frontend (librería ligera o validaciones) y backend (Pydantic + sanitización).
- Escapar datos al renderizar en cualquier vista.
- **CSP** restrictiva: solo dominios necesarios (self, Vercel, Unsplash CDN).

### Mitigación DDoS
- Rate limiting por IP (middleware en FastAPI).
- Timeouts y límites en Vercel.
- Monitorización de picos y alertas.

### Security Headers (ejemplo)
- `Content-Security-Policy: default-src 'self'; img-src 'self' https://images.unsplash.com; script-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;`
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer-when-downgrade`

---

## 6. Roadmap de ejecución paso a paso (detallado para OpenCode)
> **Nota:** cada paso debe ser un commit atómico con mensaje claro. Usar ramas `feature/*` y PRs a `develop`.

### Fase 0 — Preparación (0.5 día)
1. Crear repositorio privado en GitHub.
2. Crear ramas: `main`, `develop`, `feature/frontend`, `feature/backend`.
3. Añadir `.gitignore`, `README.md`, `.env.example`.
4. Crear estructura de carpetas:
   - `/frontend` → `index.html`, `style.css`, `app.js`, `assets/`
   - `/backend` → `main.py`, `models.py`, `schemas.py`, `database.py`, `export.py`, `utils/security.py`, `requirements.txt`
   - `/docs` → `DEPLOY.md`, `SECURITY.md`, `RUNBOOK.md`

### Fase 1 — Frontend (1 día)
1. Implementar `index.html` (formulario completo, textos en portugués, atributos en español).
2. Implementar `style.css` (Tailwind + estilos custom; responsive).
3. Implementar `app.js` con clase `FormularioMedico` (POO):
   - `constructor(formId)`
   - `obtenerDatos()`
   - `validar()` (reglas por campo)
   - `enviar()` (fetch a `/respostas`, manejo de estados)
4. Añadir mensajes UX (loading, success, error) y manejo de errores de red.
5. Pruebas manuales en Chrome/Firefox y móvil.

### Fase 2 — Backend inicial y DB (1.5 días)
1. Crear entorno virtual y `requirements.txt`.
2. Implementar `database.py` (conexión SQLAlchemy, `get_session()`).
3. Implementar `models.py` (clase `Profesor`).
4. Implementar `schemas.py` (Pydantic `ProfesorIn`, `ProfesorOut`).
5. Implementar `utils/security.py` (funciones `encrypt_field`, `decrypt_field`, `hash_password`, `verify_password`, `create_jwt`, `verify_jwt`).
6. Implementar `main.py` con `POST /respostas`:
   - Validar Pydantic.
   - Cifrar `documento` y `fiscal`.
   - Guardar en DB.
   - Log de evento.
7. Probar local con `uvicorn backend.main:app --reload`.

### Fase 3 — Seguridad y middlewares (1 día)
1. Añadir sanitización de inputs en backend (pydantic validators).
2. Implementar middleware de rate limiting (por IP).
3. Añadir security headers en todas las respuestas.
4. Implementar logging estructurado (JSON) y manejo de errores centralizado.
5. Implementar autenticación admin (endpoint `POST /admin/login` que devuelve JWT).

### Fase 4 — Panel admin y exportación (1 día)
1. Endpoint `GET /admin/respostas` (paginado, filtrable por fecha, cargo, universidad).
2. Endpoint `GET /admin/respostas/{id}` (detalle, descifrado controlado).
3. Implementar `export.py`:
   - Consulta registros.
   - Crear DataFrame con Pandas.
   - Generar `.xlsx` con OpenPyXL (encabezados en portugués).
   - Devolver `StreamingResponse` con `Content-Disposition`.
4. Añadir botón de exportar en panel admin (si se implementa UI).

### Fase 5 — Tests, CI/CD y despliegue (1 día)
1. Escribir tests básicos con `pytest` para endpoints críticos.
2. Configurar GitHub Actions:
   - Lint (flake8/black), tests, build.
3. Conectar GitHub a Vercel:
   - Configurar proyectos: frontend (carpeta `/frontend`), backend (carpeta `/backend`).
   - Añadir variables de entorno en Vercel: `DATABASE_URL`, `SECRET_KEY_AES`, `JWT_SECRET`.
4. Desplegar y verificar endpoints en staging.

### Fase 6 — Pruebas finales, documentación y entrega (0.5 día)
1. Pruebas E2E: enviar formulario, verificar DB, exportar Excel.
2. Completar `README.md`, `DEPLOY.md`, `SECURITY.md`, `RUNBOOK.md`.
3. Entrega: credenciales admin (por canal seguro), guía de operación y plan de rotación de claves.

---

## 7. Operación y mantenimiento (resumen)
- **Backups:** programar backups diarios de PostgreSQL en la plataforma elegida.
- **Monitoreo:** logs + alertas por errores 5xx y picos de tráfico.
- **Rotación de claves:** cada 90 días (documentar proceso).
- **Auditoría:** registrar quién exportó datos y cuándo.
- **Soporte:** plan de respuesta a incidentes (RUNBOOK.md).

---

--- Agents.md ---
# Agents.md

## 1. Propósito y alcance del agente
El agente es el orquestador técnico que guiará a OpenCode (o al equipo de desarrollo) para **generar, validar, desplegar y entregar** el proyecto Formulario Médico Académico. Actúa como responsable de calidad: produce artefactos, verifica seguridad, coordina CI/CD y prepara la documentación final para el cliente.

---

## 2. Roles y responsabilidades (detallado)
### Rol: Generador de código
- **Tareas:** crear archivos frontend (`index.html`, `style.css`, `app.js`) y backend (`main.py`, `models.py`, `database.py`, `export.py`, `utils/security.py`).
- **Entregables:** código limpio, modular y comentado; ejemplos de requests; scripts de inicialización.

### Rol: Arquitecto de seguridad
- **Tareas:** definir y aplicar medidas contra SQLi, XSS, DDoS; implementar cifrado AES-256; configurar security headers; documentar rotación de claves.
- **Entregables:** `SECURITY.md`, funciones de cifrado, middleware de rate limiting.

### Rol: DevOps / CI-CD
- **Tareas:** configurar repositorio privado, GitHub Actions, integración con Vercel, variables de entorno, despliegues automáticos.
- **Entregables:** workflows de GitHub Actions, `DEPLOY.md`, configuración de proyectos en Vercel.

### Rol: QA / Tester
- **Tareas:** escribir tests unitarios y de integración, ejecutar pruebas E2E, validar exportación a Excel.
- **Entregables:** suite de tests (`tests/`), reporte de pruebas.

### Rol: Documentador / Handover
- **Tareas:** crear `README.md`, `RUNBOOK.md`, guías de recuperación y operación.
- **Entregables:** documentación completa y checklist de entrega.

---

## 3. Flujo de trabajo del agente (paso a paso)
1. **Inicializar repo**: crear estructura, ramas y archivos base.
2. **Generar frontend**: producir `index.html` (textos en portugués), `style.css` (estilos), `app.js` (POO).
3. **Generar backend**: producir `database.py`, `models.py`, `schemas.py`, `main.py`, `export.py`, `utils/security.py`.
4. **Integrar cifrado**: añadir funciones `encrypt_field` y `decrypt_field` y usarlas en `POST /respostas`.
5. **Implementar autenticación admin**: endpoints de login y protección JWT.
6. **Implementar exportación**: endpoint que genera `.xlsx` y lo devuelve.
7. **Añadir middlewares**: rate limiting, security headers, logging.
8. **Escribir tests**: endpoints críticos y flujo de exportación.
9. **Configurar CI/CD**: GitHub Actions + Vercel.
10. **Desplegar y validar**: pruebas en staging y producción.
11. **Documentar y entregar**: README, DEPLOY, SECURITY, RUNBOOK.

---

## 4. Reglas de generación de código y estilo
- **Nombres:** textos visibles en portugués; `id`, `name`, `class` en español.
- **Commits:** atómicos y descriptivos (`feat: add export endpoint`, `fix: sanitize input`).
- **Calidad:** aplicar linters (black, flake8) y formateadores (prettier para JS/CSS).
- **Seguridad:** nunca hardcodear secretos; usar variables de entorno.
- **Testing:** cada endpoint crítico debe tener al menos un test automatizado.

---

## 5. Validaciones y criterios de aceptación
- **Frontend:** formulario valida campos obligatorios; UX muestra estados (loading, success, error).
- **Backend:** `POST /respostas` valida Pydantic, cifra campos sensibles y devuelve 201 con id.
- **DB:** registros persistidos con timestamps; índices creados.
- **Exportación:** archivo `.xlsx` descargable y legible en Excel/LibreOffice.
- **Seguridad:** headers presentes; rate limiting activo; no exposición de secretos.
- **CI/CD:** push a `develop` dispara tests; merge a `main` despliega en Vercel.

---

## 6. Handover y mantenimiento
- **Documentos a entregar:**
  - `README.md` (instalación local, variables de entorno).
  - `DEPLOY.md` (pasos para Vercel y restauración).
  - `SECURITY.md` (cifrado, rotación de claves, políticas).
  - `RUNBOOK.md` (procedimiento ante incidentes).
- **Checklist final:**
  - Repositorio privado con ramas protegidas.
  - Variables de entorno configuradas en Vercel.
  - Backups automáticos de DB.
  - Accesos admin entregados por canal seguro.
  - Plan de soporte y contacto para incidencias.

---

## 7. Estimación y prioridades
- **Tiempo estimado:** 6–8 días de trabajo (equipo pequeño o desarrollador senior).
- **Prioridad mínima viable (MVP):**
  1. Formulario + validaciones.
  2. Endpoint `POST /respostas` + DB.
  3. Exportación a Excel.
  4. Seguridad básica (cifrado, headers, rate limiting).
  5. CI/CD y despliegue.
- **Mejoras posteriores:** panel admin UI completo, auditoría avanzada, tests E2E automatizados, análisis estadístico integrado.

---

## Notas finales para OpenCode
- Mantener comunicación con el cliente para validar textos en portugués y requisitos legales.  
- Entregar iteraciones pequeñas y funcionales para revisión temprana.  
- Priorizar seguridad y privacidad desde el primer commit.  
- Documentar cada decisión técnica en `docs/` para auditoría futura.
