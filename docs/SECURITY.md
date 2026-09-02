# Seguridad — Formulário Médico Acadêmico

Documento de referencia sobre las medidas de seguridad implementadas y el manejo de datos sensibles (médicos y personales).

---

## 1. Amenazas y defensas implementadas

| Amenaza | Mitigación |
|---|---|
| Exposición de datos personales en DB | **Cifrado AES-256-GCM** de `documento` y `fiscal` en reposo |
| Acceso no autorizado al panel | **JWT HS256** en todos los endpoints `/api/admin/*` |
| Fuerza bruta al login | **bcrypt (coste 12)** + rate limiting por IP |
| Inyección SQL | Consultas declarativas con **SQLAlchemy** (parametrizadas); sin concatenación de SQL |
| Inyección de script (XSS) | Validación whitelist en **Pydantic** (backend) y **JS** (frontend) + escape de salida + **CSP** estricta |
| Fuga de errores internos | **Manejo centralizado de excepciones** que responde JSON sin `stacktraces` |
| Sniffing en tránsito | **HTTPS** (Vercel) + **HSTS** + conexión a Supabase con `sslmode=require` |
| Clickjacking | **`X-Frame-Options: DENY`** + CSP `frame-ancestors` |
| Confusión de algoritmo JWT | Validación estricta de `alg` (solo `HS256`; se rechaza `none`/`RS256`) |

---

## 2. Cifrado de campos sensibles

- **Algoritmo:** AES-256-GCM (autenticado — detecta alteraciones).
- **Clave:** 32 bytes, configurada como `SECRET_KEY_AES` en base64.
- **Campos cifrados:** `documento` (DNI/pasaporte) y `fiscal` (NIF). Se almacenan como `documento_enc` y `fiscal_enc`.
- **Nonce único** por operación (dos cifrados del mismo valor difieren).
- **Descifrado:** **solo** en los endpoints autenticados del panel admin (`/api/admin/respostas`, `/api/admin/respostas/{id}`, `/api/admin/exportar`). Nunca en el flujo público.
- Si no se puede descifrar un campo (clave distinta/dato corrupto), se devuelve `[indisponível]` sin romper el registro.

### ⚠️ Regla de oro: no perder la clave

`SECRET_KEY_AES` debe guardarse de forma segura (gestor de secretos). **Si se pierde, los datos cifrados son irrecuperables.**

---

## 3. Variables de entorno (secretos)

| Variable | Propósito | Sugerencia |
|---|---|---|
| `SECRET_KEY_AES` | Cifrar/descifrar campos sensibles | `openssl rand -base64 32` |
| `JWT_SECRET` | Firmar JWT | `openssl rand -hex 32` |
| `ADMIN_USER` | Usuario del panel | genérico, p. ej. `admin` |
| `ADMIN_PASSWORD_HASH` | Hash bcrypt de la contraseña | nunca la contraseña en claro |
| `DATABASE_URL` | Conexión a Supabase | pooler transaccional (6543), con credenciales |

**Nunca** se deben: commitear variables de entorno reales, loguear secretos, ni exponerlos en respuestas.

---

## 4. Rotación de claves

Rotar `SECRET_KEY_AES` **invalida** el descifrado de los datos ya almacenados (AES no tiene "clave anterior"). Procedimiento recomendado:

1. **Lineal (con re-cifrado):**
   - Descifrar con clave vieja → cifrar con clave nueva → actualizar en la DB.
   - Requiere un script que recorra los registros (solo en mantenimiento, panel cerrado).
2. **Sin re-cifrado (último recurso):** los campos existentes quedarán `[indisponível]`; solo los nuevos datos serán legibles. **Evitar** salvo emergencia.

Para `JWT_SECRET`: rotación transparente — todos los tokens emitidos antes de la rotación quedarán inválidos (los usuarios vuelven a iniciar sesión). No afecta a los datos.

---

## 5. Política de acceso y auditoría

- El panel admin (/api/admin/*) está protegido por **JWT** con expiración.
- El token se guarda en el navegador como `sessionStorage` (se limpia al cerrar pestaña o al hacer logout). **No** en `localStorage` persistente.
- Se registra en log: intentos de login fallidos, IP de origen y exportaciones generadas.

### Recomendaciones operacionales
- Cambiar la contraseña del admin cada cierto período (regenerar `ADMIN_PASSWORD_HASH`).
- Restringir acceso a producción solo a personal autorizado.
- Revisar logs ante picos de intentos de login fallidos (dicta la rotación del panel).

---

## 6. Security headers (aplicados por el middleware en el API)

```
Content-Security-Policy: default-src 'self'; img-src 'self' https://images.unsplash.com data:; script-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' data:; connect-src 'self' https://images.unsplash.com
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer-when-downgrade
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

> `script-src 'self'` prohíbe JavaScript inline: el frontend sirve scripts externos. El CSP se aplica a las respuestas del **API** (el frontend estático lo sirve directamente Vercel).

---

## 7. Cumplimiento y privacidad

Dado que se recopilan **datos médicos y personales**, se recomienda:
- Consultar la normativa aplicable (e.g. **LGPD** en Brasil, **GDPR** en Europa) y adaptar el aviso/consentimiento.
- El formulario ya exige **consentimiento informado** obligatorio antes del envío.
- Considerar minimización de datos (solo los estrictamente necesarios) y límites de retención.
