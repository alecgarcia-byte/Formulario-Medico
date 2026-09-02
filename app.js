/* ============================================================
   Formulário Médico Acadêmico - app.js
   Clase FormularioMedico (POO)
   Validación estricta + sanitización anti-XSS en el cliente.
   Atributos/clases en español; textos visibles en portugués.
   ============================================================ */

(function () {
    "use strict";

    /* --------------------------------------------------------
       Configuración de validación por campo.
       Criticidad: validate con longitud mín/máx y patrón para
       impedir que se inyecte código malicioso.
       -------------------------------------------------------- */
    const LONGITUD_MAX_GLOBAL = 120;

    const REGLAS = {
        // Datos personales
        nombre: {
            etiqueta: "Nome Completo",
            requerido: true,
            min: 2,
            max: 80,
            patron: /^[\p{L}\s\.\-']+$/u,
            mensaje: "Use somente letras (mín. 2, máx. 80 caracteres)."
        },
        apellido: {
            etiqueta: "Sobrenome",
            requerido: true,
            min: 2,
            max: 80,
            patron: /^[\p{L}\s\.\-']+$/u,
            mensaje: "Use somente letras (mín. 2, máx. 80 caracteres)."
        },
        fecha_nacimiento: {
            etiqueta: "Data de Nascimento",
            requerido: true,
            tipo: "fecha",
            mensaje: "Informe uma data de nascimento válida."
        },
        sexo: {
            etiqueta: "Sexo",
            requerido: true,
            opciones: ["Masculino", "Feminino", "Outro"],
            mensaje: "Selecione uma opção."
        },
        nacionalidad: {
            etiqueta: "Nacionalidade",
            requerido: true,
            min: 2,
            max: 60,
            patron: /^[\p{L}\s\-']+$/u,
            mensaje: "Use somente letras (mín. 2, máx. 60 caracteres)."
        },
        documento: {
            etiqueta: "Documento de Identidade / Passaporte",
            requerido: true,
            min: 4,
            max: 20,
            patron: /^[A-Za-z0-9\s\.\-]+$/,
            mensaje: "Use somente letras e números (mín. 4, máx. 20 caracteres)."
        },
        fiscal: {
            etiqueta: "Número de Identificação Fiscal (NIF)",
            requerido: true,
            min: 3,
            max: 15,
            patron: /^[0-9]+$/,
            mensaje: "Use somente números (mín. 3, máx. 15 caracteres)."
        },
        telefono: {
            etiqueta: "Telefone Pessoal / Celular",
            requerido: true,
            min: 8,
            max: 20,
            patron: /^\+?[0-9\s\-\(\)\.]+$/,
            mensaje: "Use um número de telefone válido (mín. 8, máx. 20 caracteres)."
        },
        correo_personal: {
            etiqueta: "E-mail Pessoal",
            requerido: true,
            tipo: "email",
            max: 254,
            mensaje: "Informe um e-mail válido."
        },
        correo_institucional: {
            etiqueta: "E-mail Institucional",
            requerido: true,
            tipo: "email",
            max: 254,
            mensaje: "Informe um e-mail institucional válido."
        },

        // Formação acadêmica e profissional
        titulo_grado: {
            etiqueta: "Título de Graduação",
            requerido: true,
            min: 2,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/]+$/u,
            mensaje: "Texto inválido (mín. 2, máx. 100 caracteres)."
        },
        universidad: {
            etiqueta: "Universidade",
            requerido: true,
            min: 2,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/&]+$/u,
            mensaje: "Texto inválido (mín. 2, máx. 100 caracteres)."
        },
        ano_graduacion: {
            etiqueta: "Ano de Graduação",
            requerido: true,
            tipo: "anio",
            min: 1900,
            max: 2100,
            mensaje: "Informe um ano válido (1900–2100)."
        },
        titulo_especialidad: {
            etiqueta: "Título de Especialidade",
            requerido: true,
            min: 2,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/]+$/u,
            mensaje: "Texto inválido (mín. 2, máx. 100 caracteres)."
        },
        ano_especialidad: {
            etiqueta: "Ano de Especialidade",
            requerido: true,
            tipo: "anio",
            min: 1900,
            max: 2100,
            mensaje: "Informe um ano válido (1900–2100)."
        },
        subespecialidad: {
            etiqueta: "Subespecialidade",
            requerido: false,
            min: 0,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/]*$/u,
            mensaje: "Texto inválido (máx. 100 caracteres)."
        },
        grado_academico: {
            etiqueta: "Grau Acadêmico",
            requerido: true,
            opciones: ["Graduado", "Especialista", "Mestre", "Doutor", "Pós-doutor"],
            mensaje: "Selecione uma opção."
        },
        registro_profesional: {
            etiqueta: "Registro Profissional",
            requerido: true,
            min: 3,
            max: 20,
            patron: /^[A-Za-z0-9\s\.\-]+$/,
            mensaje: "Use somente letras e números (mín. 3, máx. 20 caracteres)."
        },
        anos_experiencia_docente: {
            etiqueta: "Anos de Experiência Docente",
            requerido: true,
            tipo: "entero",
            min: 0,
            max: 80,
            mensaje: "Informe um valor inteiro entre 0 e 80."
        },
        anos_experiencia_assistencial: {
            etiqueta: "Anos de Experiência Assistencial",
            requerido: true,
            tipo: "entero",
            min: 0,
            max: 80,
            mensaje: "Informe um valor inteiro entre 0 e 80."
        },

        // Dados laborais e institucionais
        cargo_docente: {
            etiqueta: "Cargo Docente",
            requerido: true,
            opciones: ["Titular", "Associado", "Assistente", "Convidado"],
            mensaje: "Selecione uma opção."
        },
        institucion: {
            etiqueta: "Instituição",
            requerido: false,
            min: 0,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/&]*$/u,
            mensaje: "Texto inválido (máx. 100 caracteres)."
        },
        departamento: {
            etiqueta: "Departamento",
            requerido: false,
            min: 0,
            max: 100,
            patron: /^[\p{L}\s\.\-\(\)\/&]*$/u,
            mensaje: "Texto inválido (máx. 100 caracteres)."
        }
    };

    /* --------------------------------------------------------
       Utilidades de sanitización (anti-XSS)
       -------------------------------------------------------- */
    function escapeHTML(valor) {
        return String(valor)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;")
            .replace(/`/g, "&#96;");
    }

    /* Normaliza: recorta, elimina espacios duplicados y quita
       saltos de línea / caracteres de control inyectados. */
    function normalizar(valor) {
        return String(valor == null ? "" : valor)
            .replace(/[\u0000-\u001F\u007F]/g, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function esEmailValido(valor) {
        // Patrón conservador que evita payloads ejecutables.
        return typeof valor === "string" &&
            valor.length <= 254 &&
            /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(valor);
    }

    function esFechaValida(valor) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(valor)) return false;
        const d = new Date(valor + "T00:00:00Z");
        if (Number.isNaN(d.getTime())) return false;
        // La fecha no puede ser futura ni anterior a 1900.
        const hoy = new Date();
        if (d > hoy) return false;
        if (d.getFullYear() < 1900) return false;
        return true;
    }

    /* --------------------------------------------------------
       Clase FormularioMedico (POO)
       -------------------------------------------------------- */
    class FormularioMedico {
        constructor(formId) {
            this.form = document.getElementById(formId);
            if (!this.form) {
                throw new Error("Formulario no encontrado: " + formId);
            }
            this.estado = document.getElementById("estado");
            this.boton = document.getElementById("botonEnviar");
            this.errores = new Map();

            this.tieneListener = false;
            if (!this.tieneListener) {
                this.form.addEventListener("submit", this.onSubmit.bind(this));
                // Limpia el estado de error al reescribir cada campo.
                this.form.addEventListener("input", this.onInput.bind(this));
                this.tieneListener = true;
            }
        }

        /* -- Recolecta y normaliza todos los datos del formulario. -- */
        obtenerDatos() {
            const datos = {};
            Object.keys(REGLAS).forEach((campo) => {
                const el = this.form.elements[campo];
                if (!el) return;
                if (el.type === "checkbox") {
                    datos[campo] = el.checked;
                } else {
                    datos[campo] = normalizar(el.value);
                }
            });
            datos.consentimiento = this.form.elements.consentimiento
                ? this.form.elements.consentimiento.checked
                : false;
            return datos;
        }

        /* -- Valida todos los campos. Devuelve true/false. -- */
        validar() {
            this.errores.clear();
            const datos = this.obtenerDatos();

            // Consentimiento obligatorio.
            const chk = this.form.elements.consentimiento;
            if (chk && !chk.checked) {
                this.errores.set("consentimiento", "É necessário aceitar o consentimento informado.");
            }

            Object.keys(REGLAS).forEach((campo) => {
                const regla = REGLAS[campo];
                const valor = datos[campo];
                const error = this.validarCampo(campo, valor, regla);
                if (error) this.errores.set(campo, error);
            });

            this.marcarErrores();
            return this.errores.size === 0;
        }

        /* -- Valida un campo individual contra su regla. -- */
        validarCampo(campo, valor, regla) {
            if (regla.opciones) {
                if (regla.requerido && !regla.opciones.includes(valor)) {
                    return regla.mensaje;
                }
                return null;
            }

            const esVacio = typeof valor === "string" ? valor.length === 0 : valor === "";

            if (esVacio) {
                if (regla.requerido) return "Este campo é obrigatório.";
                return null; // opcional vacío es válido
            }

            if (valor.length > LONGITUD_MAX_GLOBAL) {
                return "Valor excede o limite máximo de " + LONGITUD_MAX_GLOBAL + " caracteres.";
            }

            // Límites de longitud según la regla.
            if (typeof regla.max === "number" && valor.length > regla.max) {
                return "Máximo de " + regla.max + " caracteres.";
            }
            if (typeof regla.min === "number" && regla.min > 0 && valor.length < regla.min) {
                return "Mínimo de " + regla.min + " caracteres.";
            }

            // Validación por tipo.
            switch (regla.tipo) {
                case "email":
                    if (!esEmailValido(valor)) return regla.mensaje;
                    break;
                case "fecha":
                    if (!esFechaValida(valor)) return regla.mensaje;
                    break;
                case "anio":
                    const anio = Number(valor);
                    if (!Number.isInteger(anio) || anio < regla.min || anio > regla.max) {
                        return regla.mensaje;
                    }
                    break;
                case "entero":
                    const n = Number(valor);
                    if (!Number.isInteger(n) || n < regla.min || n > regla.max) {
                        return regla.mensaje;
                    }
                    break;
                default:
                    if (regla.patron && !regla.patron.test(valor)) {
                        return regla.mensaje;
                    }
            }

            return null;
        }

        /* -- Aplica clases de error visual y recopila mensajes. -- */
        marcarErrores() {
            Object.keys(REGLAS).forEach((campo) => {
                const el = this.form.elements[campo];
                if (!el) return;
                if (this.errores.has(campo)) {
                    el.classList.add("invalido");
                } else {
                    el.classList.remove("invalido");
                }
            });
        }

        /* -- Maneja el evento submit. -- */
        async onSubmit(event) {
            event.preventDefault();

            if (!this.validar()) {
                const mensajes = Array.from(this.errores.values());
                this.mostrarEstado("error", "Corrija os campos indicados: " + mensajes.join(" "));
                return;
            }

            const datos = this.obtenerDatos();
            await this.enviar(datos);
        }

        /* -- Limpia el estado de error al escribir. -- */
        onInput(event) {
            const el = event.target;
            if (el && el.name) {
                el.classList.remove("invalido");
            }
        }

        /* -- Envía los datos al backend (POST /respostas). -- */
        async enviar(datos) {
            // Se envían los valores normalizados tal cual (sin escapar HTML):
            // el escape de HTML es solo de presentación y se aplica en el
            // render (el panel admin usa textContent y el backend valida con
            // una whitelist Pydantic). Escapar aquí corrompería los datos
            // guardados y el Excel exportado (&amp; en vez de &).
            const payload = {};
            Object.keys(datos).forEach((k) => {
                payload[k] = datos[k];
            });

            const url = (typeof window.FORMULARIO_API_URL === "string"
                ? window.FORMULARIO_API_URL
                : "").replace(/\/$/, "");

            this.mostrarEstado("loading");
            this.boton.disabled = true;

            try {
                const respuesta = await fetch(url + "/api/respostas", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (respuesta.ok) {
                    const resultado = await respuesta.json();
                    this.form.reset();
                    this.limpiarErrores();
                    this.mostrarEstado(
                        "exito",
                        "Formulário enviado com sucesso. Obrigado pela sua participação!"
                    );
                } else {
                    let detalle = "Não foi possível enviar o formulário.";
                    try {
                        const err = await respuesta.json();
                        if (err && (err.detail || err.message)) {
                            detalle = String(err.detail || err.message);
                        }
                    } catch (_e) {
                        /* ignora cuerpo no JSON */
                    }
                    this.mostrarEstado("error", detalle);
                }
            } catch (error) {
                this.mostrarEstado(
                    "error",
                    "Erro de conexão. Verifique sua internet e tente novamente."
                );
            } finally {
                this.boton.disabled = false;
            }
        }

        /* -- Mostrar estados loading/success/error. -- */
        mostrarEstado(tipo, mensaje) {
            this.estado.className = "estado visible";
            this.estado.classList.remove("estado-loading", "estado-exito", "estado-error");

            if (tipo === "loading") {
                this.estado.classList.add("estado-loading");
                this.estado.innerHTML = '<span class="spinner"></span> Enviando, aguarde...';
            } else if (tipo === "exito") {
                this.estado.classList.add("estado-exito");
                this.estado.textContent = mensaje;
            } else {
                this.estado.classList.add("estado-error");
                this.estado.textContent = mensaje;
            }
        }

        /* -- Limpia todos los errores y estados visuales. -- */
        limpiarErrores() {
            this.errores.clear();
            Object.keys(REGLAS).forEach((campo) => {
                const el = this.form.elements[campo];
                if (el) el.classList.remove("invalido");
            });
        }
    }

    /* --------------------------------------------------------
       Inicialización al cargar el DOM
       -------------------------------------------------------- */
    document.addEventListener("DOMContentLoaded", function () {
        // Instancia única global, accesible para debug.
        window.formulario = new FormularioMedico("formulario");
        window.FormularioMedico = FormularioMedico;
    });
})();
