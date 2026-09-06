-- ============================================================
-- Formulario Médico Acadêmico — Esquema completo (Supabase)
--
-- Ejecutar en: Supabase > SQL Editor > New Query > Run
--
-- Incluye:
--   1. Extensiones
--   2. Tablas (professores, admin_users, admin_sessions,
--              audit_log, export_log)
--   3. Índices
--   4. Triggers (updated_at, audit automático)
--   5. Row Level Security (RLS)
--   6. Datos iniciales (admin por defecto)
-- ============================================================

-- ============================================================
-- 1. EXTENSIONES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 2. TABLAS
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 professores — Datos del formulario (tabla principal)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS professores (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Datos personales
    nombre                      VARCHAR(80)   NOT NULL,
    apellido                    VARCHAR(80)   NOT NULL,
    fecha_nacimiento            DATE          NOT NULL,
    sexo                        VARCHAR(20)   NOT NULL
                                    CHECK (sexo IN ('Masculino','Feminino','Outro')),
    nacionalidad                VARCHAR(60)   NOT NULL,

    -- Campos sensibles (cifrados AES-256-GCM en la capa de aplicación)
    documento_enc               TEXT          NOT NULL,
    fiscal_enc                  TEXT          NOT NULL,

    telefono                    VARCHAR(20)   NOT NULL,
    correo_personal             VARCHAR(254)  NOT NULL,
    correo_institucional        VARCHAR(254)  NOT NULL,

    -- Formación académica y profesional
    titulo_grado                VARCHAR(100)  NOT NULL,
    universidad                 VARCHAR(100)  NOT NULL,
    ano_graduacion              INTEGER       NOT NULL
                                        CHECK (ano_graduacion BETWEEN 1900 AND 2100),
    titulo_especialidad         VARCHAR(100)  NOT NULL,
    ano_especialidad            INTEGER       NOT NULL
                                        CHECK (ano_especialidad BETWEEN 1900 AND 2100),
    subespecialidad             VARCHAR(100),
    grado_academico             VARCHAR(30)   NOT NULL
                                        CHECK (grado_academico IN (
                                            'Graduado','Especialista','Mestre',
                                            'Doutor','Pós-doutor')),
    registro_profesional        VARCHAR(20)   NOT NULL,
    anos_experiencia_docente    INTEGER       NOT NULL
                                        CHECK (anos_experiencia_docente BETWEEN 0 AND 80),
    anos_experiencia_assistencial INTEGER    NOT NULL
                                        CHECK (anos_experiencia_assistencial BETWEEN 0 AND 80),

    -- Datos laborales e institucionales
    cargo_docente               VARCHAR(30)
                                        CHECK (cargo_docente IS NULL OR cargo_docente IN (
                                            'Titular','Associado','Assistente','Convidado')),
    institucion                 VARCHAR(100),
    departamento                VARCHAR(100),

    -- Consentimiento informado (obligatorio para cumplimiento RGPD/LGPD)
    consentimiento              BOOLEAN       NOT NULL DEFAULT false,

    -- Origen de la petición (rate limiting y trazabilidad)
    ip_origen                   VARCHAR(45),
    user_agent                  TEXT,

    -- Auditoría
    created_at                  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ   NOT NULL DEFAULT now(),

    -- Soft delete (nunca se borran datos médicos)
    deleted_at                  TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- 2.2 admin_users — Usuarios administradores del panel
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50)   NOT NULL UNIQUE,
    password_hash   VARCHAR(255),  -- obsoleto: el acceso es por URL JWT
    email           VARCHAR(254),
    is_active       BOOLEAN       NOT NULL DEFAULT true,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 2.3 admin_sessions — Sesiones JWT activas (revocación)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- En el acceso por URL (JWT) no hay usuario admin: columna nullable.
    admin_user_id   UUID          REFERENCES admin_users(id) ON DELETE CASCADE,
    token_jti       VARCHAR(36)   NOT NULL UNIQUE,   -- JWT ID para revocación
    ip_origen       VARCHAR(45),
    user_agent      TEXT,
    expira_en       TIMESTAMPTZ   NOT NULL,
    revocado        BOOLEAN       NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 2.4 audit_log — Registro de auditoría (cumplimiento RGPD/LGPD)
--
-- Cada operación sobre datos sensibles se registra aquí.
-- Tablas auditadas: professores, admin_users, admin_sessions.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tabla           VARCHAR(50)   NOT NULL,
    registro_id     UUID,
    accion          VARCHAR(20)   NOT NULL
                        CHECK (accion IN ('INSERT','UPDATE','DELETE','SELECT','LOGIN','LOGOUT')),
    admin_user_id   UUID          REFERENCES admin_users(id) ON DELETE SET NULL,
    ip_origen       VARCHAR(45),
    user_agent      TEXT,
    datos_antes     JSONB,        -- snapshot antes del cambio (UPDATE/DELETE)
    datos_despues   JSONB,        -- snapshot después del cambio (INSERT/UPDATE)
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 2.5 export_log — Registro de exportaciones Excel
--
-- Cada descarga de Excel se registra para trazabilidad.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS export_log (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_user_id           UUID          REFERENCES admin_users(id) ON DELETE SET NULL,
    ip_origen               VARCHAR(45),
    registros_exportados    INTEGER       NOT NULL CHECK (registros_exportados >= 0),
    nombre_archivo          VARCHAR(255),
    filtros_aplicados       JSONB,        -- {"cargo":"Assistente","universidad":"USP"}
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ============================================================
-- 3. ÍNDICES
-- ============================================================

-- professores: consultas frecuentes del panel admin
CREATE INDEX IF NOT EXISTS ix_professores_correo_institucional
    ON professores (correo_institucional);
CREATE INDEX IF NOT EXISTS ix_professores_registro_profesional
    ON professores (registro_profesional);
CREATE INDEX IF NOT EXISTS ix_professores_created_at
    ON professores (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_professores_cargo_docente
    ON professores (cargo_docente);
CREATE INDEX IF NOT EXISTS ix_professores_universidad
    ON professores (universidad);
CREATE INDEX IF NOT EXISTS ix_professores_sexo
    ON professores (sexo);
CREATE INDEX IF NOT EXISTS ix_professores_grado_academico
    ON professores (grado_academico);
-- Soft delete: solo registros activos
CREATE INDEX IF NOT EXISTS ix_professores_active
    ON professores (deleted_at) WHERE deleted_at IS NULL;

-- admin_users
CREATE INDEX IF NOT EXISTS ix_admin_users_username
    ON admin_users (username);

-- admin_sessions
CREATE INDEX IF NOT EXISTS ix_admin_sessions_token_jti
    ON admin_sessions (token_jti);
CREATE INDEX IF NOT EXISTS ix_admin_sessions_admin_user_id
    ON admin_sessions (admin_user_id);
CREATE INDEX IF NOT EXISTS ix_admin_sessions_expira_en
    ON admin_sessions (expira_en);

-- audit_log: consultas de trazabilidad
CREATE INDEX IF NOT EXISTS ix_audit_log_tabla
    ON audit_log (tabla);
CREATE INDEX IF NOT EXISTS ix_audit_log_registro_id
    ON audit_log (registro_id);
CREATE INDEX IF NOT EXISTS ix_audit_log_admin_user_id
    ON audit_log (admin_user_id);
CREATE INDEX IF NOT EXISTS ix_audit_log_created_at
    ON audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_log_accion
    ON audit_log (accion);

-- export_log
CREATE INDEX IF NOT EXISTS ix_export_log_admin_user_id
    ON export_log (admin_user_id);
CREATE INDEX IF NOT EXISTS ix_export_log_created_at
    ON export_log (created_at DESC);

-- ============================================================
-- 4. TRIGGERS
-- ============================================================

-- 4.1 updated_at automático (professores + admin_users)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_updated_at ON professores;
CREATE TRIGGER trg_updated_at
    BEFORE UPDATE ON professores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_updated_at ON admin_users;
CREATE TRIGGER trg_updated_at
    BEFORE UPDATE ON admin_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 4.2 Auditoría automática en professores (INSERT/UPDATE/DELETE)
CREATE OR REPLACE FUNCTION audit_professores()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, datos_despues)
        VALUES ('professores', NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, datos_antes, datos_despues)
        VALUES ('professores', NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, datos_antes)
        VALUES ('professores', OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_professores ON professores;
CREATE TRIGGER trg_audit_professores
    AFTER INSERT OR UPDATE OR DELETE ON professores
    FOR EACH ROW
    EXECUTE FUNCTION audit_professores();

-- ============================================================
-- 5. ROW LEVEL SECURITY (RLS)
--
-- En Supabase, el backend se conecta como service_role (bypass RLS).
-- RLS protege la BD por si se accede desde el Dashboard o desde
-- el cliente directamente (nunca debería ocurrir, pero es defense-in-depth).
-- ============================================================

ALTER TABLE professores      ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users      ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_sessions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log        ENABLE ROW LEVEL SECURITY;
ALTER TABLE export_log       ENABLE ROW LEVEL SECURITY;

-- Políticas: SOLO el rol service_role (el backend) puede acceder.
-- Restringimos con `TO service_role` para que anon/authenticated NO tengan
-- acceso a ninguna tabla, aunque RLS esté activa.
CREATE POLICY "service_role_full_access" ON professores
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON admin_users
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON admin_sessions
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON audit_log
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON export_log
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- ============================================================
-- 6. DATOS INICIALES
-- ============================================================
--
-- El panel admin usa acceso por URL JWT de acceso único (sin usuario/
-- contraseña). Por eso NO se insertan usuarios admin por defecto.
-- La tabla admin_users se conserva únicamente por compatibilidad esquemática
-- con las sesiones/auditoría (admin_user_id es nullable).

-- ============================================================
-- LISTO
--
-- La BD está lista. Ahora puedes conectar el backend vía:
--
--   DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
--
-- Verificar con:
--   curl https://<tu-dominio>.vercel.app/api/health
-- ============================================================
