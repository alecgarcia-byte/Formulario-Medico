/* 404.js - Página 404 personalizada (ruta no encontrada).
   Script externo para respetar la CSP `script-src 'self'` de vercel.json.
   Selector de idioma PT/ES/EN coherente con el formulario. */

(function () {
    "use strict";

    var TEXTOS = {
        pt: {
            mensaje: "Página não encontrada",
            descripcion: "O endereço que você acessou não existe, foi movido ou está temporariamente indisponível.",
            volver: "Voltar ao formulário"
        },
        es: {
            mensaje: "Página no encontrada",
            descripcion: "La dirección que accediste no existe, fue movida o está temporalmente no disponible.",
            volver: "Volver al formulario"
        },
        en: {
            mensaje: "Page not found",
            descripcion: "The address you accessed does not exist, has been moved, or is temporarily unavailable.",
            volver: "Back to the form"
        }
    };

    function idiomaActual() {
        var actual = "pt";
        try {
            actual = localStorage.getItem("formulario_idioma") || "pt";
        } catch (e) { /* sin almacenamiento */ }
        return TEXTOS[actual] ? actual : "pt";
    }

    function aplicar(idioma) {
        var t = TEXTOS[idioma] || TEXTOS.pt;
        var main = document.querySelector("main.contenedor-404");
        if (!main) return;

        document.documentElement.setAttribute("lang", idioma);
        main.setAttribute("lang", idioma);

        var el = main.querySelector("[data-i18n='mensaje']");
        if (el) el.textContent = t.mensaje;
        el = main.querySelector("[data-i18n='descripcion']");
        if (el) el.textContent = t.descripcion;
        el = main.querySelector("[data-i18n='volver']");
        if (el) el.textContent = t.volver;

        var botones = document.querySelectorAll(".selector-idioma button");
        botones.forEach(function (b) {
            b.setAttribute(
                "aria-pressed",
                b.getAttribute("data-idioma") === idioma ? "true" : "false"
            );
        });
    }

    function init() {
        var botones = document.querySelectorAll(".selector-idioma button");
        botones.forEach(function (b) {
            b.addEventListener("click", function () {
                var id = b.getAttribute("data-idioma");
                try { localStorage.setItem("formulario_idioma", id); } catch (e) { /* ignore */ }
                aplicar(id);
            });
        });
        aplicar(idiomaActual());
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
