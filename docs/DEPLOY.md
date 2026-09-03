# Guía de Despliegue (DEPLOY) — Formulário Médico Acadêmico

Este documento detalla, paso a paso, cómo desplegar el sistema en **Vercel** (frontend estático + backend FastAPI serverless) con **Supabase** (PostgreSQL). Está pensado para que lo ejecutes tú (el cliente), ya que requiere acceso a tus cuentas.

---

## 0. Arquitectura resumida

```
Internet
   │
   ├── https://<tu-dominio>.vercel.app/                  -> index.html (formulario)
   ├── https://<tu-dominio>.vercel.app/admin-<TOKEN>     -> panel admin (URL secreta)
   │
   └── https://<tu-dominio>.vercel.app/api/*             -> FastAPI (serverless)
                                                           └── se conecta a Supabase (PostgreSQL)
```

- **Frontend:** estático en la raíz de Vercel (`index.html`, `style.css`, `app.js`, `pico.min.css` — librería de UI CSS-only autohospedada, sin CDN externo).
- **Panel admin:** servido por el backend en `/admin-<TOKEN>` donde `<TOKEN>` es el valor de `ADMIN_TOKEN`. **No hay login de usuario/contraseña**: el acceso se protege con una URL/llave secreta.
- **Backend:** `api/index.py` expone la app FastAPI en `/api/*`.
- **Base de datos:** PostgreSQL en **Supabase** (la única DB; se eliminaron Neon y Railway).

> **Importante:** `porphyria/panel_admin.html` es la plantilla del panel. El backend la sirve en `/admin-<TOKEN>` e inyecta el token real para que el JavaScript (`porphyria.js`) llame a la API protegida `/api/admin/<TOKEN>/...`.

---

## 1. Crear el proyecto en Supabase

1. Ve a <https://supabase.com> e inicia sesión o crea una cuenta.
2. Clic en **New project**:
   - **Name:** `formulario-papa`
   - **Database Password:** genera una segura y **guárdala** (la vas a necesitar).
   - **Region:** la más cercana a tu público (ej. `South America (São Paulo)`).
3. Espera a que el proyecto termine de aprovisionarse.

### 1.1 Obtener la connection string (pooler en modo transacción)

Con la arquitectura **serverless (Vercel)**, es obligatorio usar el **pooler de Supabase en modo transacción** (puerto **6543**). El modo sesión (5432) agota conexiones en serverless.

1. En el dashboard de tu proyecto, ve a **Project Settings → Database → Connection string**.
2. En **Connection pooling** (transaccional), selecciona **Transaction mode** (puerto 6543), lenguaje **Python**, y copia la cadena tipo:
   ```
   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
   > Reemplaza `<password>` por la contraseña real de la base de datos.

### 1.2 Crear la tabla

La aplicación crea la tabla automáticamente al arrancar (`Base.metadata.create_all`). Para un despliegue correcto en producción, sin embargo, recomendamos crearla **antes** con el script SQL/Python provisto.

Desde **Supabase → SQL Editor**, se puede ejecutar el SQL correspondiente al modelo `Profesor`. La forma más simple y portátil es generar la tabla desde nuestro código:

```bash
# Desde la raíz del proyecto, con las dependencias instaladas:
DATABASE_URL="postgresql://postgres.<ref>:<password>@...:6543/postgres" \
  python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

> En Supabase el esquema por defecto es `public` y el usuario `postgres` es el `service_role` con permisos para crear tablas. Si despliegas en Vercel con el runtime de Python, la tabla también puede crearse al primer arranque.

---

## 2. Repositorio en GitHub

1. Crea un repositorio **privado** (los datos son médicos).
2. Sube el contenido de la carpeta del proyecto (no subas `backend/venv/` ni `*.db`).
3. Recomendado: añade un `.gitignore` con:
   ```
   backend/venv/
   *.db
   .env
   __pycache__/
   ```

---

## 3. Variables de entorno (¡críticas!)

Todas se cargan desde variables de entorno (nunca hardcodeadas). Configura estas en **Vercel (Project → Settings → Environment Variables)** y también en tu `.env` local.

| Variable | Requerida | Descripción |
|---|---|---|
| `DATABASE_URL` | ✔ | Cadena del pooler transaccional de Supabase (puerto 6543) |
| `SECRET_KEY_AES` | ✔ | Clave AES-256 (32 bytes en base64) para campos sensibles |
| `ADMIN_TOKEN` | ✔ | URL/llave secreta de acceso al panel admin (mín. 20 caracteres) |
| `ENVIRONMENT` | opcional | `production` valida secretos al arranque y deshabilita `/docs` de FastAPI |
| `FRONTEND_URL` | opcional | URL del frontend (se agrega a CORS) |

> `JWT_SECRET` ya no es necesario para el acceso al panel (se eliminó el login con JWT). Puedes omitirlo.

### Generar las claves

```bash
# SECRET_KEY_AES (32 bytes -> base64)
openssl rand -base64 32

# ADMIN_TOKEN (URL/llave secreta del panel, hex de 32 bytes)
openssl rand -hex 32
# O bien:  node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

> **¡Nunca** repitas `SECRET_KEY_AES` entre entornos si no quieres poder migrar datos cifrados entre ellos — y **nunca** lo pierdas**, porque los campos cifrados no podrán descifrarse.
>
> `ADMIN_TOKEN` es la **URL de acceso al panel**: quien tenga la URL puede ver los datos. Guárdala en secreto y compártela solo con el personal autorizado.

---

## 4. Conexión a Vercel y despliegue

### 4.1 Frontend (estático) + Backend (FastAPI) en un solo proyecto

La carpeta raíz contiene todo (`index.html`, `porphyria/`, `api/`, `backend/`). Vercel detecta:

- `api/index.py` → función serverless Python (FastAPI), montada en `/api/*`.
- Archivos estáticos del resto → servidos en su ruta.

### 4.2 `vercel.json` (ya incluido en el repo)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    { "source": "/admin-([^/]+)", "destination": "/api" },
    { "source": "/api/(.*)", "destination": "/api" }
  ]
}
```

- `/admin-<TOKEN>` → enruta al backend FastAPI, que sirve el panel solo si el token coincide con `ADMIN_TOKEN` (si no, responde 404).
- `/api/*` → enruta al backend FastAPI (que expone sus propias rutas `/api/...`).

### 4.3 Pasos en Vercel

1. Ve a <https://vercel.com> → **Add New → Project**.
2. Importa tu repositorio de GitHub.
3. En **Environment Variables**, pega las variables de la sección 3 (incluye `ADMIN_TOKEN`).
4. **Framework Preset:** *Other* (o déjalo en blanco).
5. **Build Command:** vacío (no se compila nada; es estático + serverless).
6. Clic en **Deploy**.

> Nota sobre la versión de Python: Vercel usa su runtime de Python. Verifica que la versión soportada por Vercel sea compatible con las dependencias (`pandas`, `psycopg2-binary`, etc.). Si Vercel no ofrece la versión local (3.14), ajusta el pin en `requirements.txt` (raíz) a la versión compatible (p. ej. 3.12/3.13).

### 4.4 Verificación post-despliegue

```bash
# Salud del API
curl https://<tu-dominio>.vercel.app/api/health

# Panel admin (abre en el navegador con tu ADMIN_TOKEN real)
# https://<tu-dominio>.vercel.app/admin-<ADMIN_TOKEN>
# Un token incorrecto debe devolver 404 (no revela el panel).
```

Prueba todo el flujo: enviar el formulario, entrar al panel `https://<tu-dominio>.vercel.app/admin-<ADMIN_TOKEN>`, ver los resultados descifrados y descargar el Excel.

---

## 5. Comandos útiles

| Acción | Comando |
|---|---|
| Tests | `python -m pytest backend/tests` (o `cd backend && python -m pytest`) |
| Backend en local | `uvicorn backend.main:app --reload` (desde la raíz) |
| Frontend en local | abrir `index.html` con Live Server; definir `FORMULARIO_API_URL` si el backend no está en el mismo origen |

> Los tests del backend usan una **base SQLite temporal aislada y auto-limpia**
> (variable `SQLITE_PATH`); no tocan `formulario_local.db` ni dejan datos de
> prueba en el repositorio.

---

## 6. Checklist de despliegue

- [ ] Proyecto Supabase creado y connection string (puerto 6543) copiada.
- [ ] Tabla creada (o arranque que la cree).
- [ ] Variables de entorno en Vercel (todas las requeridas, incluida `ADMIN_TOKEN`).
- [ ] Repo privado en GitHub conectado a Vercel.
- [ ] `vercel.json` presente en la raíz.
- [ ] Deploy exitoso y `/api/health` responde.
- [ ] `/admin-<ADMIN_TOKEN>` muestra el panel y permite exportar Excel; un token incorrecto devuelve 404.
