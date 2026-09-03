# Seguridad — Formulário Médico Acadêmico

Documento de referencia sobre las medidas de seguridad implementadas y el manejo de datos sensibles (médicos y personales).

---

## 1. Amenazas y defensas implementadas

| Amenaza | Mitigación |
|---|---|
| Exposición de datos personales en DB | **Cifrado AES-256-GCM** de `documento` y `fiscal` en reposo |
| Acceso no autorizado al panel | **URL/llave secreta `ADMIN_TOKEN`** en la ruta (`/admin-<token>`), validada con comparación constante (`hmac.compare_digest`); tokens inválidos devuelven **404** sin revelar la existencia del panel |
| Adivinación/fuerza bruta de la llave del panel | Llave larga y aleatoria (mín. 20 caracteres, recomendado 32+ bytes hex) generada con `openssl rand -hex 32` + rate limiting por IP |
| Inyección SQL | Consultas declarativas con **SQLAlchemy** (parametrizadas); sin concatenación de SQL |
| Inyección de script (XSS) | Validación whitelist en **Pydantic** (backend) y **JS** (frontend) + escape de salida + **CSP** estricta |
| Fuga de errores internos | **Manejo centralizado de excepciones** que responde JSON sin `stacktraces` |
| Sniffing en tránsito | **HTTPS** (Vercel) + **HSTS** + conexión a Supabase con `sslmode=require` |
| Clickjacking | **`X-Frame-Options: DENY`** + CSP `frame-ancestors 'none'` |

> **Nota:** el acceso al panel **no** usa usuario/contraseña ni JWT. Se protege por una **URL secreta** (`ADMIN_TOKEN`): quien no conozca el token no puede cargar el panel ni consumir la API admin (respuestas 404).

---

## 2. Cifrado de campos sensibles

- **Algoritmo:** AES-256-GCM (autenticado — detecta alteraciones).
- **Clave:** 32 bytes, configurada como `SECRET_KEY_AES` en base64.
- **Campos cifrados:** `documento` (DNI/pasaporte) y `fiscal` (NIF). Se almacenan como `documento_enc` y `fiscal_enc`.
- **Nonce único** por operación (dos cifrados del mismo valor difieren).
- **Descifrado:** **solo** en los endpoints autenticados del panel admin (`/api/admin/{token}/respostas`, `/api/admin/{token}/respostas/{id}`, `/api/admin/{token}/exportar`). Nunca en el flujo público.
- Si no se puede descifrar un campo (clave distinta/dato corrupto), se devuelve `[indisponível]` sin romper el registro.

### ⚠️ Regla de oro: no perder la clave

`SECRET_KEY_AES` debe guardarse de forma segura (gestor de secretos). **Si se pierde, los datos cifrados son irrecuperables.**

---

## 3. Variables de entorno (secretos)

| Variable | Propósito | Sugerencia |
|---|---|---|
| `SECRET_KEY_AES` | Cifrar/descifrar campos sensibles | `openssl rand -base64 32` |
| `ADMIN_TOKEN` | URL/llave secreta del panel admin (acceso) | `openssl rand -hex 32`; mín. 20 caracteres |
| `DATABASE_URL` | Conexión a Supabase | pooler transaccional (6543), con credenciales |
| `JWT_SECRET` | Reservado (ya no se usa para el acceso al panel) | opcional |
| `FRONTEND_URL` | URL del frontend para CORS | opcional |
| `ENVIRONMENT` | `production` valida secretos y deshabilita `/docs` | opcional |

**Nunca** se deben: commitear variables de entorno reales, loguear secretos, ni exponerlos en respuestas. En desarrollo, la falta de `ADMIN_TOKEN` genera uno temporal aleatorio por proceso (con aviso por log).

---

## 4. Rotación de claves

- **`SECRET_KEY_AES`:** rotarla **invalida** el descifrado de los datos ya almacenados (AES no tiene "clave anterior"). Procedimiento recomendado:
  1. **Lineal (con re-cifrado):** descifrar con clave vieja → cifrar con clave nueva → actualizar en la DB. Requiere un script que recorra los registros (solo en mantenimiento, panel cerrado).
  2. **Sin re-cifrado (último recurso):** los campos existentes quedarán `[indisponível]`; solo los nuevos datos serán legibles. **Evitar** salvo emergencia.
- **`ADMIN_TOKEN`:** rotarlo es **transparente** y no afecta a los datos ni a nadie: cambia la URL de acceso al panel. Al rotarlo, la URL anterior deja de servir de inmediato. Recomendado de forma periódica y **obligatorio tras una brecha o sospecha de filtración**.

---

## 5. Política de acceso y auditoría

- El panel admin se sirve en `/admin-<token>` y la API admin en `/api/admin/<token>/...`, ambos protegidos por `ADMIN_TOKEN`.
- El token **vive en el HTML** servido por el backend (inyectado en la plantilla) y **no** se guarda en `sessionStorage`/`localStorage` del navegador. No hay contraseña que gestionar.
- Un token incorrecto (o la ausencia de él) devuelve **404**, de modo que el panel/API no se descubre por escaneo.
- Se registra en log: accesos a la API admin (listados, detalles) y exportaciones generadas.

### Recomendaciones operacionales
- **Rotar `ADMIN_TOKEN`** de forma periódica y tras cualquier brecha.
- Restringir el conocimiento de la URL del panel solo a personal autorizado.
- Revisar logs de accesos a la API admin y exportaciones ante actividad inusual.

---

## 6. Security headers (aplicados por el middleware en el API)

```
Content-Security-Policy: default-src 'self'; img-src 'self' data: https://images.unsplash.com; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

> `script-src 'self'` prohíbe JavaScript inline: el frontend sirve scripts externos. El CSP se aplica a las respuestas del **API** (el frontend estático lo sirve directamente Vercel).

---

## 7. Cumplimiento y privacidad

Dado que se recopilan **datos médicos y personales**, se recomienda:
- Consultar la normativa aplicable (e.g. **LGPD** en Brasil, **GDPR** en Europa) y adaptar el aviso/consentimiento.
- El formulario ya exige **consentimiento informado** obligatorio antes del envío.
- Considerar minimización de datos (solo los estrictamente necesarios) y límites de retención.
