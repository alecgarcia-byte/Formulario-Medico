# Runbook — Formulário Médico Acadêmico

Procedimientos operacionales para monitorizar, diagnosticar y responder ante incidentes.

---

## 1. Chequeo de salud (health check)

Endpoint: `GET /api/health`

```bash
curl -s https://<tu-dominio>.vercel.app/api/health
# Devuelve: {"status": "ok", "service": "formulario-api"}
```

- **200 OK** → API viva.
- **Error 5xx** → la función serverless o la BD tienen problemas (ver §3).

---

## 2. Monitorización y logs

- **Vercel:** *Project → Logs*. Verás los logs de la función serverless (FastAPI). Busca mensajes con prefijo `formulario` (nivel INFO/ERROR).
- **Supabase:** *Database → Logs* para consultas y conexiones.
- Datos útiles a vigilar:
  - `Login admin fallido` — posible fuerza bruta.
  - `Erro ao persistir resposta` — fallo de escritura (transacciones, bloqueos, cuota).
  - Rate limiting activo (respuestas `429 Too many requests`).

---

## 3. Diagnóstico rápido de problemas

### 3.1 El formulario no guarda
1. ¿`/api/health` responde? Si no → problema de la función/pipeline.
2. Revisa el log `Erro ao persistir resposta`.
3. Verifica `DATABASE_URL`, `SECRET_KEY_AES`, `JWT_SECRET` en Vercel env vars.
4. Comprueba que la tabla `professores` existe y el rol tiene permisos de INSERT.

### 3.2 El panel `/porphyria` no carga
1. ¿La página muestra el login? Si no → rewrite de `/porphyria` en `vercel.json`.
2. ¿Login falla siempre? Verifica `ADMIN_USER` y `ADMIN_PASSWORD_HASH` (hash bcrypt correcto).
3. Revisa los logs por `Login admin fallido`.

### 3.3 Exportación da error
- El error `Não foi possível gerar a exportação` suele venir de `CifradoError` al descifrar. Esto ocurre si `SECRET_KEY_AES` cambió o los datos fueron cifrados con otra clave.
- Revisa la sección de cifrado en `SECURITY.md`.

### 3.4 Error 429 "Too many requests"
- Rate limiting global (60 req/60 s por IP). Uso normal no lo dispara; un exceso puntual es esperable. Se auto-resetea en 60 s.

---

## 4. Procedimientos ante incidentes

### 4.1 Datos cifrados irrecuperables (clave perdida)
- **Impacto:** los campos `documento`/`fiscal` existentes quedan `[indisponível]`.
- **Acción:** restaurar `SECRET_KEY_AES` desde el gestor de secretos.
- **Prevención:** rotación de claves NOTA en `SECURITY.md`.

### 4.2 Brecha / sospecha de acceso no autorizado
1. **Rotar** `ADMIN_PASSWORD_HASH` (nueva contraseña + `ADMIN_PASSWORD_HASH`).
2. **Rotar** `JWT_SECRET` (invalida tokens existentes).
3. **Rotar** `DATABASE_URL` (nuevas credenciales en Supabase -> reset password).
4. Revisar logs de login y exportaciones recientes.
5. Si aplica, notificar conforme a normativa (LGPD/GDPR) y a los afectados.

### 4.3 Base de datos llena / cuota superada
1. Supabase *Project Settings → Database → Storage/Usage*.
2. Exportar `.xlsx` como respaldo, luego depurar/archivar registros antiguos.
3. Aumentar plan si el crecimiento es esperado.

### 4.4 Despliegue roto
1. En Vercel, usar **Rollback** a un deployment anterior estable.
2. Revisar el log del build/function.
3. Verificar que las env vars no cambiaron entre deploys.

---

## 5. Tareas periódicas recomendadas

| Frecuencia | Tarea |
|---|---|
| Diaria | Revisar `/api/health` y logs de errores |
| Semanal | Revisar intentos de login fallidos (fuerza bruta) |
| Mensual | Respaldo/exportación de datos; revisar cuota de Supabase |
| Trimestral | Revisar si algo puede endurecerse (config, claves) |

---

## 6. Datos de contacto / error

- Reportar problemas en el repositorio (issues) con: endpoint, status code, body de error (sin datos personales) y hora UTC.
