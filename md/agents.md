# Agents.md

# Propósito del agente
El agente actúa como **orquestador técnico y operativo** para la creación, despliegue y entrega del proyecto Formulario Médico Académico. Su misión es coordinar tareas, generar artefactos de código, aplicar buenas prácticas de seguridad, validar resultados y preparar la documentación y el handover final para el cliente. El agente debe garantizar que el producto sea seguro, auditable, escalable y listo para análisis estadístico.

---

# Alcance y responsabilidades
**Responsabilidades principales**
- Planificar y dividir el proyecto en tareas ejecutables y priorizadas.
- Generar el código base del frontend y backend conforme a las especificaciones.
- Configurar la infraestructura de despliegue y CI/CD.
- Implementar medidas de seguridad en todas las capas.
- Probar, validar y documentar el sistema.
- Entregar un paquete final con instrucciones operativas y de mantenimiento.

**Entregables**
- Repositorio privado en GitHub con ramas y protección.
- Frontend completo (`index.html`, `style.css`, `app.js`).
- Backend completo (FastAPI): `main.py`, `models.py`, `schemas.py`, `database.py`, `export.py`, `utils/security.py`.
- Scripts y workflows de CI/CD (GitHub Actions).
- Documentación: `README.md`, `DEPLOY.md`, `SECURITY.md`, `RUNBOOK.md`.
- Suite de tests básicos (`tests/`).
- Aplicación desplegada en Vercel y base de datos en PostgreSQL (Railway/Neon).
- Plan de rotación de claves y runbook de incidentes.

---

# Habilidades y roles necesarios
**Habilidades técnicas**
- Frontend: HTML semántico, TailwindCSS, CSS avanzado, JavaScript Vanilla con POO, accesibilidad.
- Backend: Python 3.10+, FastAPI, Pydantic, SQLAlchemy, Uvicorn.
- Base de datos: PostgreSQL, modelado relacional, índices, migraciones con Alembic.
- Seguridad: cifrado AES-256-GCM, hashing bcrypt, Content-Security-Policy, rate limiting, sanitización de entradas.
- Exportación: Pandas, OpenPyXL para generación de Excel.
- DevOps: GitHub, GitHub Actions, Vercel, gestión de secretos.
- QA: pytest, pruebas manuales E2E, validación de exportación.

**Roles operativos**
- Arquitecto de software: define la arquitectura y revisa decisiones críticas.
- Desarrollador frontend: implementa UI, validaciones y UX.
- Desarrollador backend: implementa API, modelos y seguridad.
- Ingeniero DevOps: configura CI/CD y despliegue.
- QA/Tester: crea y ejecuta pruebas.
- Documentador: redacta guías y runbooks.

---

# Flujo de trabajo y orquestación paso a paso
## Preparación del repositorio y entorno
1. Crear repositorio privado en GitHub.
2. Configurar ramas protegidas: `main` y `develop`. Crear plantillas de PR y reglas de merge.
3. Añadir `.gitignore`, `README.md` y `.env.example` con variables necesarias.
4. Crear estructura de carpetas:
   - `/frontend`
   - `/backend`
   - `/docs`
   - `/tests`
5. Definir convenciones de commits y branching (ej. Conventional Commits).

## Desarrollo frontend
1. Crear `index.html` con formulario completo dividido en secciones; textos en portugués; atributos técnicos en español.
2. Implementar `style.css` con Tailwind y estilos custom: paleta, tipografía, animaciones, responsividad y accesibilidad.
3. Implementar `app.js` con POO:
   - Clase `FormularioMedico` con métodos `constructor(formId)`, `obtenerDatos()`, `validar()`, `enviar()`, `mostrarEstado()`.
   - Manejo de estados: loading, success, error.
   - Sanitización básica en cliente y prevención de XSS en valores mostrados.
4. Añadir mensajes de consentimiento informado y checkbox obligatorio antes de enviar.
5. Probar en navegadores y dispositivos móviles; corregir problemas de UX.

## Desarrollo backend y base de datos
1. Crear entorno virtual y `requirements.txt` con dependencias: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic`, `python-dotenv`, `cryptography`, `pandas`, `openpyxl`, `bcrypt`, `pytest`.
2. Implementar `database.py`:
   - Conexión segura a PostgreSQL usando `DATABASE_URL` desde variables de entorno.
   - Función `get_session()` para sesiones de DB.
3. Implementar `models.py` con SQLAlchemy:
   - Modelo `Profesor` con columnas y tipos adecuados.
   - Índices en `correo_institucional`, `registro_profesional`, `created_at`.
4. Implementar `schemas.py` con Pydantic:
   - `ProfesorIn` para entrada, `ProfesorOut` para salida.
   - Validadores para formatos y rangos.
5. Implementar `utils/security.py`:
   - Funciones `encrypt_field(plaintext)`, `decrypt_field(ciphertext)` usando AES-256-GCM.
   - Funciones `hash_password`, `verify_password` con bcrypt.
   - Funciones JWT `create_jwt(payload)`, `verify_jwt(token)`.
6. Implementar `main.py` con FastAPI:
   - Middleware para security headers y rate limiting.
   - Endpoint `POST /respostas` que:
     - Valida `ProfesorIn`.
     - Cifra `documento` y `fiscal`.
     - Inserta registro en DB con `created_at`.
     - Devuelve `201` con `id`.
   - Endpoints admin protegidos:
     - `POST /admin/login` → devuelve JWT.
     - `GET /admin/respostas` → paginado y filtrable.
     - `GET /admin/respostas/{id}` → detalle con descifrado controlado.
     - `GET /admin/exportar` → genera y devuelve `.xlsx`.

## Exportación y panel admin
1. Implementar `export.py`:
   - Consulta registros según filtros.
   - Construye DataFrame con Pandas.
   - Formatea columnas y encabezados en portugués.
   - Genera `.xlsx` con OpenPyXL y estilos básicos (encabezados en negrita, ancho de columnas).
   - Devuelve `StreamingResponse` con `Content-Disposition`.
2. Implementar paginación y filtros en `GET /admin/respostas`.
3. Registrar auditoría de exportaciones: quién exportó y cuándo.

## Seguridad y hardening
1. Aplicar sanitización de entradas en backend y validación estricta con Pydantic.
2. Implementar rate limiting por IP y por endpoint crítico.
3. Añadir security headers en todas las respuestas.
4. Asegurar que la clave AES y JWT estén en variables de entorno y no en el repo.
5. Implementar logging estructurado y manejo centralizado de errores.
6. Revisar dependencias y aplicar actualizaciones de seguridad.

## Tests, CI y despliegue
1. Escribir tests unitarios y de integración con pytest para endpoints críticos.
2. Configurar GitHub Actions:
   - Workflow para `push` a `develop`: lint, tests.
   - Workflow para `merge` a `main`: despliegue en Vercel.
3. Conectar repositorio a Vercel:
   - Configurar proyecto frontend apuntando a `/frontend`.
   - Configurar proyecto backend apuntando a `/backend` (serverless).
   - Añadir variables de entorno en Vercel: `DATABASE_URL`, `SECRET_KEY_AES`, `JWT_SECRET`, `ADMIN_USER`, `ADMIN_PASSWORD_HASH`.
4. Ejecutar despliegue y validar endpoints en staging.

## Entrega y handover
1. Ejecutar pruebas E2E: enviar formulario, verificar DB, exportar Excel.
2. Completar documentación: `README.md`, `DEPLOY.md`, `SECURITY.md`, `RUNBOOK.md`.
3. Entregar credenciales admin por canal seguro y plan de rotación de claves.
4. Programar sesión de handover con el cliente para explicar operación y mantenimiento.

---

# Reglas operativas y estándares de calidad
**Convenciones de código**
- Mensajes de commit claros y atómicos.
- Branching: `feature/*` → `develop` → `main`.
- Pull requests con descripción, checklist y reviewers asignados.

**Estilo y linters**
- Python: `black`, `flake8`.
- JavaScript: `prettier`, reglas básicas de ESLint.
- CSS: organización modular y uso de variables para paleta.

**Seguridad**
- Nunca almacenar secretos en el repositorio.
- Revisiones de seguridad antes de mergear a `main`.
- Tests de seguridad básicos: inyección, XSS, autenticación.

**Documentación**
- Cada módulo debe incluir docstrings y comentarios clave.
- `SECURITY.md` debe contener instrucciones de cifrado y rotación de claves.
- `DEPLOY.md` debe describir pasos para restauración y rollback.

---

# Criterios de aceptación y checklist final
**Criterios mínimos**
- Formulario funcional y validado en cliente y servidor.
- Datos persistidos en PostgreSQL con campos sensibles cifrados.
- Endpoint de exportación a Excel funcionando y descargable.
- Panel admin protegido con JWT y paginación.
- Despliegue automático en Vercel desde GitHub.
- Documentación completa y runbook entregado.

**Checklist**
- [ ] Repositorio privado creado y ramas protegidas.
- [ ] Frontend implementado y responsivo.
- [ ] Backend con endpoints y seguridad.
- [ ] DB con tabla `professores` y migraciones.
- [ ] Exportación a Excel verificada.
- [ ] Tests automatizados ejecutándose en CI.
- [ ] Variables de entorno configuradas en Vercel.
- [ ] Documentación y runbook entregados.
- [ ] Plan de rotación de claves y backups configurado.

---

# Estimación de tiempo y prioridades
**Estimación total:** 6 a 8 días de trabajo por un desarrollador senior o equipo pequeño.  
**Prioridades para MVP**
1. Formulario y validaciones.
2. Endpoint `POST /respostas` y persistencia en DB.
3. Exportación a Excel.
4. Seguridad básica (cifrado, headers, rate limiting).
5. CI/CD y despliegue.

---

# Notas finales para OpenCode
- Mantener comunicación continua con el cliente para validar textos en portugués y requisitos legales sobre datos personales.  
- Entregar iteraciones pequeñas y funcionales para revisión temprana.  
- Priorizar la seguridad y la privacidad desde el primer commit.  
- Documentar cada decisión técnica en la carpeta `docs/` para auditoría futura.
