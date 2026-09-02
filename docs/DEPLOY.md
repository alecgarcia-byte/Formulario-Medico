# Guía de Despliegue (DEPLOY) — Formulário Médico Acadêmico

Este documento detalla, paso a paso, cómo desplegar el sistema en **Vercel** (frontend estático + backend FastAPI serverless) con **Supabase** (PostgreSQL). Está pensado para que lo ejecutes tú (el cliente), ya que requiere acceso a tus cuentas.

---

## 0. Arquitectura resumida

```
Internet
   │
   ├── https://<tu-dominio>.vercel.app/            -> index.html (formulario)
   ├── https://<tu-dominio>.vercel.app/porphyria   -> panel admin (porphyria.html)
   │
   └── https://<tu-dominio>.vercel.app/api/*       -> FastAPI (serverless)
                                                    └── se conecta a Supabase (PostgreSQL)
```

- **Frontend:** estático en la raíz de Vercel (`index.html`, `style.css`, `app.js`).
- **Panel admin:** `porphyria/porphyria.html` servido en `/porphyria`.
- **Backend:** `api/index.py` expone la app FastAPI en `/api/*`.
- **Base de datos:** PostgreSQL en **Supabase** (la única DB; se eliminaron Neon y Railway).

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
| `JWT_SECRET` | ✔ | Secreto para firmar el JWT del panel admin |
| `ADMIN_USER` | ✔ | Usuario del panel admin |
| `ADMIN_PASSWORD_HASH` | ✔ | Hash **bcrypt** de la contraseña del admin |
| `ENVIRONMENT` | opcional | `production` deshabilita `/docs` de FastAPI |
| `FRONTEND_URL` | opcional | URL del frontend (se agrega a CORS) |

### Generar las claves

```bash
# SECRET_KEY_AES (32 bytes -> base64)
openssl rand -base64 32

# JWT_SECRET (hex de 32 bytes)
openssl rand -hex 32

# ADMIN_PASSWORD_HASH (bcrypt). Coste recomendado 12.
python -c "import bcrypt; print(bcrypt.hashpw(b'MISENHA', bcrypt.gensalt(rounds=12)).decode())"
```

> **¡Nunca** repitas `SECRET_KEY_AES` entre entornos si no quieres poder migrar datos cifrados entre ellos — y **nunca** lo pierdas**, porque los campos cifrados no podrán descifrarse.

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
    { "source": "/porphyria", "destination": "/porphyria/porphyria.html" },
    { "source": "/api/(.*)", "destination": "/api" }
  ]
}
```

- `/porphyria` → sirve el panel admin.
- `/api/*` → enruta al backend FastAPI (que expone sus propias rutas `/api/...`).

### 4.3 Pasos en Vercel

1. Ve a <https://vercel.com> → **Add New → Project**.
2. Importa tu repositorio de GitHub.
3. En **Environment Variables**, pega las variables de la sección 3.
4. **Framework Preset:** *Other* (o déjalo en blanco).
5. **Build Command:** vacío (no se compila nada; es estático + serverless).
6. Clic en **Deploy**.

> Nota sobre la versión de Python: Vercel usa su runtime de Python. Verifica que la versión soportada por Vercel sea compatible con las dependencias (`pandas`, `psycopg2-binary`, etc.). Si Vercel no ofrece la versión local (3.14), ajusta el pin en `requirements.txt` (raíz) a la versión compatible (p. ej. 3.12/3.13).

### 4.4 Verificación post-despliegue

```bash
# Salud del API
curl https://<tu-dominio>.vercel.app/api/health

# Panel admin
# Abre https://<tu-dominio>.vercel.app/porphyria
```

Prueba todo el flujo: enviar el formulario, entrar al panel `/porphyria`, ver los resultados descifrados y descargar el Excel.

---

## 5. Comandos útiles

| Acción | Comando |
|---|---|
| Tests | `python -m pytest backend/tests` (o `cd backend && python -m pytest`) |
| Backend en local | `uvicorn backend.main:app --reload` (desde la raíz) |
| Frontend en local | abrir `index.html` con Live Server; definir `FORMULARIO_API_URL` si el backend no está en el mismo origen |

---

## 6. Checklist de despliegue

- [ ] Proyecto Supabase creado y connection string (puerto 6543) copiada.
- [ ] Tabla creada (o arranque que la cree).
- [ ] Variables de entorno en Vercel (todas las requeridas).
- [ ] Repo privado en GitHub conectado a Vercel.
- [ ] `vercel.json` presente en la raíz.
- [ ] Deploy exitoso y `/api/health` responde.
- [ ] `/porphyria` muestra el panel y permite login + exportar Excel.
