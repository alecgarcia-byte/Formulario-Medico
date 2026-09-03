/* ============================================================
   Formulário Médico Acadêmico - app.js
   Clase FormularioMedico (POO)
   Validación estricta + sanitización anti-XSS en el cliente.
   Atributos/clases en español; textos visibles en portugués.
   ============================================================ */

(function () {
    "use strict";

    /* --------------------------------------------------------
       Internacionalización (PT / ES / EN). Sin librerías.
       PT es el idioma por defecto. La preferencia se guarda en
       localStorage. Los textos dinámicos (validación/estado) se
       traducen con t() y tpl().
       -------------------------------------------------------- */
    const CLAVE_LOCAL_STORAGE = "formulario_papa_idioma";
    let idiomaActual = "pt";

    const IDIOMAS = {
        pt: {
            textos: {
                titulo: "Formulário Médico Acadêmico",
                subtitulo: "Pesquisa para professores por especialidade. Seus dados serão tratados com confidencialidade e usados exclusivamente para fins acadêmicos e estatísticos.",
                paso1: "Dados Pessoais",
                paso2: "Formação",
                paso3: "Laboral",
                secao1: "Dados Pessoais",
                secao2: "Formação Acadêmica e Profissional",
                secao3: "Dados Laborais e Institucionais",
                consentimiento: "Declaro que entendi as informações sobre a pesquisa e autorizo o tratamento dos meus dados pessoais, de forma confidencial e com finalidade exclusivamente acadêmica e estatística.",
                enviar: "Enviar",
                loading: "Enviando",
                loadingEstado: "Enviando, aguarde..."
            },
            etiquetas: {
                nombre: "Nome Completo", apellido: "Sobrenome", fecha_nacimiento: "Data de Nascimento",
                sexo: "Sexo", nacionalidad: "Nacionalidade", documento: "Documento de Identidade / Passaporte",
                fiscal: "Número de Identificação Fiscal (NIF)", telefono: "Telefone Pessoal / Celular",
                correo_personal: "E-mail Pessoal", correo_institucional: "E-mail Institucional",
                titulo_grado: "Título de Graduação", universidad: "Universidade que conferiu o título",
                ano_graduacion: "Ano de Graduação", titulo_especialidad: "Título de Especialidade",
                ano_especialidad: "Ano de obtenção do título de especialista", subespecialidad: "Subespecialidade",
                grado_academico: "Grau Acadêmico", registro_profesional: "Registro Profissional",
                anos_experiencia_docente: "Anos de Experiência Docente", anos_experiencia_assistencial: "Anos de Experiência Assistencial",
                cargo_docente: "Cargo Docente", institucion: "Instituição", departamento: "Departamento"
            },
            placeholders: {
                nombre: "António Santos", nacionalidad: "Portugal", fecha_nacimiento: "10/10/1990",
                telefono: "123 456 789", ano_graduacion: "2026"
            },
            opciones: {
                sexo: { selecionar: "Selecione...", Masculino: "Masculino", Feminino: "Feminino", Outro: "Outro" },
                grado_academico: { selecionar: "Selecione...", Graduado: "Graduado", Especialista: "Especialista", Mestre: "Mestre", Doutor: "Doutor", "Pós-doutor": "Pós-doutor" },
                cargo_docente: { selecionar: "Selecione...", Titular: "Titular", Associado: "Associado", Assistente: "Assistente", Convidado: "Convidado" }
            },
            mensajes: {
                obrigatorio: "Este campo é obrigatório.",
                selecionarOpcion: "Selecione uma opção.",
                excede: "Valor excede o limite máximo de {max} caracteres.",
                maxCar: "Máximo de {max} caracteres.",
                minCar: "Mínimo de {min} caracteres.",
                emailInvalido: "Informe um e-mail válido.",
                emailInstInvalido: "Informe um e-mail institucional válido.",
                fechaInvalida: "Informe uma data de nascimento válida.",
                anioInvalido: "Informe um ano válido ({min}–{max}).",
                enteroInvalido: "Informe um valor inteiro entre {min} e {max}.",
                patronLetras: "Use somente letras (mín. {min}, máx. {max} caracteres).",
                patronLetNum: "Use somente letras e números (mín. {min}, máx. {max} caracteres).",
                patronNumero: "Use somente números (mín. {min}, máx. {max} caracteres).",
                patronTelefono: "Use um número de telefone válido (mín. {min}, máx. {max} caracteres).",
                patronTexto: "Texto inválido (mín. {min}, máx. {max} caracteres).",
                consentimiento: "É necessário aceitar o consentimento informado.",
                corrigir: "Corrija os campos indicados: ",
                exito: "Formulário enviado com sucesso. Obrigado pela sua participação!",
                erroEnviar: "Não foi possível enviar o formulário.",
                erroConexao: "Erro de conexão. Verifique sua internet e tente novamente."
            }
        },
        es: {
            textos: {
                titulo: "Formulario Médico Académico",
                subtitulo: "Investigación para profesores por especialidad. Sus datos serán tratados con confidencialidad y utilizados exclusivamente con fines académicos y estadísticos.",
                paso1: "Datos Personales",
                paso2: "Formación",
                paso3: "Laboral",
                secao1: "Datos Personales",
                secao2: "Formación Académica y Profesional",
                secao3: "Datos Laborales e Institucionales",
                consentimiento: "Declaro que he entendido la información sobre la investigación y autorizo el tratamiento de mis datos personales, de forma confidencial y con finalidad exclusivamente académica y estadística.",
                enviar: "Enviar",
                loading: "Enviando",
                loadingEstado: "Enviando, espere..."
            },
            etiquetas: {
                nombre: "Nombre Completo", apellido: "Apellido", fecha_nacimiento: "Fecha de Nacimiento",
                sexo: "Sexo", nacionalidad: "Nacionalidad", documento: "Documento de Identidad / Pasaporte",
                fiscal: "Número de Identificación Fiscal (NIF)", telefono: "Teléfono Personal / Celular",
                correo_personal: "Correo Electrónico Personal", correo_institucional: "Correo Electrónico Institucional",
                titulo_grado: "Título de Grado", universidad: "Universidad que confirió el título",
                ano_graduacion: "Año de Graduación", titulo_especialidad: "Título de Especialidad",
                ano_especialidad: "Año de obtención del título de especialista", subespecialidad: "Subespecialidad",
                grado_academico: "Grado Académico", registro_profesional: "Registro Profesional",
                anos_experiencia_docente: "Años de Experiencia Docente", anos_experiencia_assistencial: "Años de Experiencia Asistencial",
                cargo_docente: "Cargo Docente", institucion: "Institución", departamento: "Departamento"
            },
            placeholders: {
                nombre: "António Santos", nacionalidad: "Portugal", fecha_nacimiento: "10/10/1990",
                telefono: "123 456 789", ano_graduacion: "2026"
            },
            opciones: {
                sexo: { selecionar: "Seleccione...", Masculino: "Masculino", Feminino: "Femenino", Outro: "Otro" },
                grado_academico: { selecionar: "Seleccione...", Graduado: "Graduado", Especialista: "Especialista", Mestre: "Máster", Doutor: "Doctor", "Pós-doutor": "Posdoctorado" },
                cargo_docente: { selecionar: "Seleccione...", Titular: "Titular", Associado: "Asociado", Assistente: "Asistente", Convidado: "Invitado" }
            },
            mensajes: {
                obrigatorio: "Este campo es obligatorio.",
                selecionarOpcion: "Seleccione una opción.",
                excede: "El valor excede el límite máximo de {max} caracteres.",
                maxCar: "Máximo de {max} caracteres.",
                minCar: "Mínimo de {min} caracteres.",
                emailInvalido: "Introduzca un correo electrónico válido.",
                emailInstInvalido: "Introduzca un correo electrónico institucional válido.",
                fechaInvalida: "Introduzca una fecha de nacimiento válida.",
                anioInvalido: "Introduzca un año válido ({min}–{max}).",
                enteroInvalido: "Introduzca un valor entero entre {min} y {max}.",
                patronLetras: "Use solo letras (mín. {min}, máx. {max} caracteres).",
                patronLetNum: "Use solo letras y números (mín. {min}, máx. {max} caracteres).",
                patronNumero: "Use solo números (mín. {min}, máx. {max} caracteres).",
                patronTelefono: "Use un número de teléfono válido (mín. {min}, máx. {max} caracteres).",
                patronTexto: "Texto no válido (mín. {min}, máx. {max} caracteres).",
                consentimiento: "Es necesario aceptar el consentimiento informado.",
                corrigir: "Corrija los campos indicados: ",
                exito: "Formulario enviado con éxito. ¡Gracias por su participación!",
                erroEnviar: "No fue posible enviar el formulario.",
                erroConexao: "Error de conexión. Verifique su internet e inténtelo de nuevo."
            }
        },
        en: {
            textos: {
                titulo: "Academic Medical Form",
                subtitulo: "Research for teachers by specialty. Your data will be treated confidentially and used exclusively for academic and statistical purposes.",
                paso1: "Personal Data",
                paso2: "Education",
                paso3: "Work",
                secao1: "Personal Data",
                secao2: "Academic and Professional Education",
                secao3: "Work and Institutional Data",
                consentimiento: "I declare that I have understood the information about the research and authorize the processing of my personal data, confidentially and exclusively for academic and statistical purposes.",
                enviar: "Submit",
                loading: "Sending",
                loadingEstado: "Sending, please wait..."
            },
            etiquetas: {
                nombre: "Full Name", apellido: "Last Name", fecha_nacimiento: "Date of Birth",
                sexo: "Sex", nacionalidad: "Nationality", documento: "Identity Document / Passport",
                fiscal: "Tax Identification Number (NIF)", telefono: "Personal Phone / Mobile",
                correo_personal: "Personal Email", correo_institucional: "Institutional Email",
                titulo_grado: "Degree Title", universidad: "University that conferred the degree",
                ano_graduacion: "Year of Graduation", titulo_especialidad: "Specialty Title",
                ano_especialidad: "Year the specialist title was obtained", subespecialidad: "Subspecialty",
                grado_academico: "Academic Degree", registro_profesional: "Professional Registration",
                anos_experiencia_docente: "Years of Teaching Experience", anos_experiencia_assistencial: "Years of Clinical Experience",
                cargo_docente: "Teaching Position", institucion: "Institution", departamento: "Department"
            },
            placeholders: {
                nombre: "António Santos", nacionalidad: "Portugal", fecha_nacimiento: "10/10/1990",
                telefono: "123 456 789", ano_graduacion: "2026"
            },
            opciones: {
                sexo: { selecionar: "Select...", Masculino: "Male", Feminino: "Female", Outro: "Other" },
                grado_academico: { selecionar: "Select...", Graduado: "Graduate", Especialista: "Specialist", Mestre: "Master", Doutor: "Doctor", "Pós-doutor": "Postdoctoral" },
                cargo_docente: { selecionar: "Select...", Titular: "Chair", Associado: "Associate", Assistente: "Assistant", Convidado: "Visiting" }
            },
            mensajes: {
                obrigatorio: "This field is required.",
                selecionarOpcion: "Select an option.",
                excede: "Value exceeds the maximum limit of {max} characters.",
                maxCar: "Maximum of {max} characters.",
                minCar: "Minimum of {min} characters.",
                emailInvalido: "Enter a valid email address.",
                emailInstInvalido: "Enter a valid institutional email address.",
                fechaInvalida: "Enter a valid date of birth.",
                anioInvalido: "Enter a valid year ({min}–{max}).",
                enteroInvalido: "Enter an integer between {min} and {max}.",
                patronLetras: "Use letters only (min. {min}, max. {max} characters).",
                patronLetNum: "Use letters and numbers only (min. {min}, max. {max} characters).",
                patronNumero: "Use numbers only (min. {min}, max. {max} characters).",
                patronTelefono: "Enter a valid phone number (min. {min}, max. {max} characters).",
                patronTexto: "Invalid text (min. {min}, max. {max} characters).",
                consentimiento: "You must accept the informed consent.",
                corrigir: "Correct the indicated fields: ",
                exito: "Form submitted successfully. Thank you for your participation!",
                erroEnviar: "The form could not be sent.",
                erroConexao: "Connection error. Check your internet connection and try again."
            }
        }
    };

    /* Devuelve el texto simple para una clave del idioma actual. */
    function t(clave) {
        const v = IDIOMAS[idiomaActual].textos[clave];
        if (typeof v === "string") return v;
        return IDIOMAS.pt.textos[clave] || clave;
    }

    /* Devuelve un texto con plantilla {min}/{max} sustituidos. */
    function tpl(clave, params) {
        let s = t(clave);
        if (s == null) s = clave;
        if (params) {
            s = s.replace(/\{min\}/g, params.min)
                 .replace(/\{max\}/g, params.max);
        }
        return s;
    }

    /* Clave de plantilla de mensaje para cada campo con validación por patio. */
    const PATRONES_POR_CAMPO = {
        nombre: "patronLetras",
        apellido: "patronLetras",
        nacionalidad: "patronLetras",
        documento: "patronLetNum",
        registro_profesional: "patronLetNum",
        fiscal: "patronNumero",
        telefono: "patronTelefono",
        titulo_grado: "patronTexto",
        universidad: "patronTexto",
        titulo_especialidad: "patronTexto",
        subespecialidad: "patronTexto",
        institucion: "patronTexto",
        departamento: "patronTexto"
    };

    /* Traduce el mensaje de un campo según el tipo y sus límites. */
    function mensajePatron(campo, regla) {
        const min = regla.min || 0;
        const max = regla.max || LONGITUD_MAX_GLOBAL;
        let clave;
        if (regla.tipo === "email") {
            clave = (campo === "correo_institucional") ? "emailInstInvalido" : "emailInvalido";
        } else if (regla.tipo === "fecha") {
            clave = "fechaInvalida";
        } else if (regla.tipo === "anio") {
            return tpl("anioInvalido", { min: regla.min, max: regla.max });
        } else if (regla.tipo === "entero") {
            return tpl("enteroInvalido", { min: regla.min, max: regla.max });
        } else {
            clave = PATRONES_POR_CAMPO[campo] || "patronTexto";
        }
        return tpl(clave, { min: min, max: max });
    }

    /* Aplica el idioma: actualiza DOM, selects, placeholders y REGLAS. */
    function aplicarIdioma(lang) {
        if (!IDIOMAS[lang]) lang = "pt";
        idiomaActual = lang;
        const d = IDIOMAS[lang];

        document.documentElement.lang = (lang === "pt") ? "pt-BR" : (lang === "es" ? "es" : "en");

        // Textos estáticos marcados con data-i18n.
        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            const key = el.getAttribute("data-i18n");
            if (key && d.textos[key] !== undefined) {
                el.textContent = d.textos[key];
            }
        });

        // Etiquetas de los campos (label for = name).
        Object.keys(d.etiquetas).forEach(function (name) {
            const label = document.querySelector('label[for="' + name + '"]');
            if (label) label.textContent = d.etiquetas[name];
        });

        // Placeholders.
        Object.keys(d.placeholders).forEach(function (name) {
            const el = document.getElementById(name);
            if (el && el.getAttribute("placeholder") !== null) {
                el.setAttribute("placeholder", d.placeholders[name]);
            }
        });

        // Opciones de los selects.
        Object.keys(d.opciones).forEach(function (selName) {
            const sel = document.getElementById(selName);
            if (!sel) return;
            const mapa = d.opciones[selName];
            Array.prototype.forEach.call(sel.options, function (opt) {
                if (opt.value === "") {
                    opt.textContent = mapa.selecionar;
                } else if (mapa[opt.value] !== undefined) {
                    opt.textContent = mapa[opt.value];
                }
            });
        });

        // Botón.
        const boton = document.getElementById("botonEnviar");
        if (boton) boton.textContent = d.textos.enviar;

        // Reflexiona el idioma activo en los botones del selector.
        document.querySelectorAll(".idioma-btn").forEach(function (btn) {
            const activo = btn.getAttribute("data-idioma") === lang;
            btn.setAttribute("aria-pressed", activo ? "true" : "false");
            btn.classList.toggle("activo", activo);
        });

        // Guarda la preferencia.
        try {
            localStorage.setItem(CLAVE_LOCAL_STORAGE, lang);
        } catch (e) { /* localStorage no disponible */ }
    }

    function idiomaGuardado() {
        try {
            const v = localStorage.getItem(CLAVE_LOCAL_STORAGE);
            return (v === "es" || v === "en" || v === "pt") ? v : "pt";
        } catch (e) {
            return "pt";
        }
    }

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

            this.configurarContadores();
            this.configurarToast();
        }

        /* -- Crea contadores de caracteres y checks decorativos por campo. -- */
        configurarContadores() {
            const camposTexto = this.form.querySelectorAll(
                "input[type=text], input[type=email], input[type=tel]"
            );
            camposTexto.forEach((el) => {
                const campo = el.closest(".campo");
                if (!campo) return;
                // Contador de caracteres (solo si hay límite útil en la regla).
                const max = REGLAS[el.name] ? REGLAS[el.name].max : null;
                if (max && max < 120) {
                    const contador = document.createElement("div");
                    contador.className = "campo-contador";
                    campo.appendChild(contador);
                    el.__contador = contador;
                }
                // Check decorativo de contenido válido.
                campo.classList.add("campo-pos");
                const ok = document.createElement("span");
                ok.className = "entrada-ok";
                ok.innerHTML =
                    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
                ok.setAttribute("aria-hidden", "true");
                campo.appendChild(ok);
                el.__ok = ok;
            });
        }

        /* -- Prepara un contenedor global de toast para feedback. -- */
        configurarToast() {
            if (document.getElementById("toast-liquid")) return;
            const toast = document.createElement("div");
            toast.id = "toast-liquid";
            toast.setAttribute("role", "status");
            toast.setAttribute("aria-live", "polite");
            document.body.appendChild(toast);
            this.toast = toast;
        }

        /* -- Muestra un toast transitorio (éxito/error). -- */
        mostrarToast(mensaje, tipo) {
            if (!this.toast) return;
            this.toast.textContent = mensaje;
            this.toast.className = "toast visible toast-" + (tipo || "info");
            clearTimeout(this.toast.__t);
            this.toast.__t = setTimeout(() => {
                this.toast.classList.remove("visible");
            }, 3600);
        }

        /* -- Actualiza el contador de caracteres de un campo. -- */
        actualizarContador(el) {
            const c = el.__contador;
            if (!c) return;
            const max = REGLAS[el.name] ? REGLAS[el.name].max : null;
            const n = el.value.length;
            c.textContent = n + " / " + max;
            c.classList.add("visible");
            c.classList.toggle("cerca", n >= max * 0.85 && n < max);
            c.classList.toggle("limite", n >= max);
        }

        /* -- Actualiza el check decorativo según haya contenido válido. -- */
        actualizarCheck(el) {
            const ok = el.__ok;
            if (!ok) return;
            const dato = normalizar(el.value);
            const regla = REGLAS[el.name];
            const pareceValido =
                dato.length > 0 &&
                (!regla || this.validarCampo(el.name, dato, regla) === null);
            ok.classList.toggle("mostrar", pareceValido);
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
                this.errores.set("consentimiento", t("consentimiento"));
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
                    return t("selecionarOpcion");
                }
                return null;
            }

            const esVacio = typeof valor === "string" ? valor.length === 0 : valor === "";

            if (esVacio) {
                if (regla.requerido) return t("obrigatorio");
                return null; // opcional vacío es válido
            }

            if (valor.length > LONGITUD_MAX_GLOBAL) {
                return tpl("excede", { max: LONGITUD_MAX_GLOBAL });
            }

            // Límites de longitud según la regla.
            if (typeof regla.max === "number" && valor.length > regla.max) {
                return tpl("maxCar", { max: regla.max });
            }
            if (typeof regla.min === "number" && regla.min > 0 && valor.length < regla.min) {
                return tpl("minCar", { min: regla.min });
            }

            // Validación por tipo.
            switch (regla.tipo) {
                case "email":
                    if (!esEmailValido(valor)) return mensajePatron(campo, regla);
                    break;
                case "fecha":
                    if (!esFechaValida(valor)) return mensajePatron(campo, regla);
                    break;
                case "anio":
                    const anio = Number(valor);
                    if (!Number.isInteger(anio) || anio < regla.min || anio > regla.max) {
                        return mensajePatron(campo, regla);
                    }
                    break;
                case "entero":
                    const n = Number(valor);
                    if (!Number.isInteger(n) || n < regla.min || n > regla.max) {
                        return mensajePatron(campo, regla);
                    }
                    break;
                default:
                    if (regla.patron && !regla.patron.test(valor)) {
                        return mensajePatron(campo, regla);
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
                this.mostrarEstado("error", t("corrigir") + mensajes.join(" "));
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
                this.actualizarContador(el);
                this.actualizarCheck(el);
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
                    this.mostrarEstado("exito", t("exito"));
                } else {
                    let detalle = t("erroEnviar");
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
                this.mostrarEstado("error", t("erroConexao"));
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
                this.estado.innerHTML = '<span class="spinner"></span> ' + t("loadingEstado");
                // Refleja el estado en el propio botón (morphing).
                this.boton.classList.add("btn-carga");
                this.boton.innerHTML = '<span class="spinner" style="border-top-color:#fff;border-color:rgba(255,255,255,.4)"></span> ' + t("loading");
            } else {
                this.boton.classList.remove("btn-carga");
                this.boton.textContent = t("enviar");
                if (tipo === "exito") {
                    this.estado.classList.add("estado-exito");
                    this.estado.textContent = mensaje;
                    this.mostrarToast(mensaje, "exito");
                    this.celebrar();
                } else {
                    this.estado.classList.add("estado-error");
                    this.estado.textContent = mensaje;
                    this.mostrarToast(mensaje, "error");
                }
            }
        }

        /* -- Efecto "celebración" (pulso del título/header + estela + confeti). -- */
        celebrar() {
            const header = document.querySelector(".contenedor-formulario");
            if (header) {
                header.classList.remove("pulso");
                void header.offsetWidth; // reinicia la animación
                header.classList.add("pulso");
            }
            this.confeti();
        }

        /* -- Confeti líquido (partículas orgánicas breves). -- */
        confeti(cantidad) {
            const n = cantidad || 26;
            const colores = [
                "#1E40AF", "#2563EB", "#7C3AED", "#10B981",
                "#60A5FA", "#F59E0B", "#EC4899",
            ];
            const cx = window.innerWidth / 2;
            const y0 = window.innerHeight * 0.42;
            for (let i = 0; i < n; i++) {
                const p = document.createElement("i");
                p.className = "estallido";
                const tam = 7 + Math.random() * 9;
                p.style.cssText =
                    "left:" + (cx + (Math.random() - 0.5) * 120) + "px;" +
                    "top:" + y0 + "px;" +
                    "width:" + tam + "px;height:" + tam + "px;" +
                    "background:" + colores[i % colores.length] + ";" +
                    "--dx:" + ((Math.random() - 0.5) * 260) + "px;" +
                    "--dy:" + ((-150 - Math.random() * 180)) + "px;" +
                    "animation-delay:" + (Math.random() * 0.2) + "s";
                document.body.appendChild(p);
                (function (el) {
                    setTimeout(function () {
                        if (el.parentNode) el.parentNode.removeChild(el);
                    }, 1200);
                })(p);
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

        // --- Selector de idioma (PT / ES / EN) ---
        const botonesIdioma = document.querySelectorAll(".idioma-btn");
        botonesIdioma.forEach(function (btn) {
            btn.addEventListener("click", function () {
                aplicarIdioma(btn.getAttribute("data-idioma"));
            });
        });
        aplicarIdioma(idiomaGuardado());

        // --- Microinteracción: indicador de passos (stepper) ---
        // Solo UI; no afecta la validación ni el envío.
        const stepper = document.querySelector(".stepper");
        if (stepper) {
            const pasos = Array.from(stepper.querySelectorAll(".step"));
            const secciones = pasos
                .map((p) => document.getElementById(p.dataset.objetivo))
                .filter(Boolean);

            function actualizarStepper() {
                let activo = pasos.length - 1;
                secciones.forEach((seccion, i) => {
                    if (seccion.getBoundingClientRect().top <= window.innerHeight * 0.5) {
                        activo = i;
                    }
                });
                // Marca como "completo" los pasos anteriores si tienen contenido.
                pasos.forEach((p, i) => {
                    p.classList.toggle("ativo", i === activo);
                    const sec = secciones[i];
                    p.classList.toggle(
                        "completo",
                        i < activo && sec && sec.querySelectorAll("input, select").length > 0
                    );
                });
            }

            const observer = new IntersectionObserver(
                actualizarStepper,
                { threshold: 0.05 }
            );
            secciones.forEach((s) => observer.observe(s));

            // Click en un paso: desplazamiento suave a la sección.
            pasos.forEach((p) => {
                p.addEventListener("click", function () {
                    const sec = document.getElementById(p.dataset.objetivo);
                    if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
                });
                p.style.cursor = "pointer";
            });

            window.addEventListener("scroll", actualizarStepper, { passive: true });
            actualizarStepper();
        }
    });
})();
