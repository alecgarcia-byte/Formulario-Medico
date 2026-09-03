/* porphyria.js - Painel admin (ruta /admin-<token>) · sem login.
   O acesso é por URL/llave secreta (ADMIN_TOKEN) injetado pelo backend. */

(function () {
    "use strict";

    const API_BASE = (typeof window.FORMULARIO_API_URL === "string"
        ? window.FORMULARIO_API_URL
        : "").replace(/\/$/, "");

    // Token leído del attr data-admin-token (evita scripts inline bloqueados por
    // la CSP `script-src 'self'`). Fallback a window.ADMIN_TOKEN por compatibilidad.
    const TOKEN =
        (document.body && document.body.dataset && document.body.dataset.adminToken) ||
        (window.ADMIN_TOKEN || "");

    const $resultados = document.getElementById("vista-resultados");
    const $estadoResultados = document.getElementById("estado-resultados");
    const $tablaBody = document.querySelector("#tabla-resultados tbody");
    const $resumen = document.getElementById("resumen-total");
    const $botonExportar = document.getElementById("botao-exportar");
    const $botonSair = document.getElementById("botao-sair");
    const $botonFiltrar = document.getElementById("botao-filtrar");
    const $filtroCargo = document.getElementById("filtro-cargo");
    const $filtroUniversidade = document.getElementById("filtro-universidade");

    /* ---------- Utilitários ---------- */

    function setEstado(el, mensaje, tipo) {
        el.textContent = mensaje || "";
        el.className = "estado" + (tipo ? " " + tipo : "");
    }

    function urlAdmin(accion, filtros) {
        const params = new URLSearchParams();
        if (filtros && filtros.cargo) params.set("cargo", filtros.cargo);
        if (filtros && filtros.universidade) params.set("universidade", filtros.universidade);
        const qs = params.toString();
        return API_BASE + "/api/admin/" + encodeURIComponent(TOKEN) + "/" + accion +
            (qs ? "?" + qs : "");
    }

    /* ---------- Lista e exportação ---------- */

    async function listarRespostas(filtros) {
        // Solo se muestra la vista si hay token válido; si no, 404/inexistente.
        const resposta = await fetch(urlAdmin("respostas", filtros));
        if (!resposta.ok) {
            throw new Error("Não foi possível carregar os resultados.");
        }
        return await resposta.json();
    }

    function preencherTabla(items) {
        // Esqueleto (skeleton) mientras se espera la primera carga.
        $tablaBody.innerHTML = "";
        if (!items) {
            let filas = 0;
            while (filas < 5) {
                const tr = document.createElement("tr");
                tr.className = "skeleton-fila";
                for (let c = 0; c < 7; c++) {
                    const td = document.createElement("td");
                    td.innerHTML = '<span class="skeleton"></span>';
                    tr.appendChild(td);
                }
                $tablaBody.appendChild(tr);
                filas++;
            }
            return;
        }
        if (items.length === 0) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 7;
            td.textContent = "Nenhum resultado encontrado.";
            td.style.textAlign = "center";
            td.style.padding = "32px";
            td.style.color = "var(--color-texto-suave)";
            tr.appendChild(td);
            $tablaBody.appendChild(tr);
            return;
        }
        items.forEach(function (item, idx) {
            const tr = document.createElement("tr");
            tr.style.animationDelay = idx * 0.04 + "s";
            tr.classList.add("reveal-fila");
            [
                item.id,
                (item.nombre || "") + " " + (item.apellido || ""),
                item.documento,
                item.fiscal,
                item.universidad,
                item.cargo_docente,
                item.created_at ? new Date(item.created_at).toLocaleString() : ""
            ].forEach(function (valor) {
                const td = document.createElement("td");
                td.textContent = valor == null ? "" : String(valor);
                tr.appendChild(td);
            });
            $tablaBody.appendChild(tr);
        });
    }

    async function carregarResultados() {
        // Skeleton loader durante la carga.
        preencherTabla(null);
        setEstado($estadoResultados, "Carregando resultados...", "carregando");
        try {
            const dados = await listarRespostas({
                cargo: $filtroCargo.value,
                universidade: $filtroUniversidade.value.trim()
            });
            preencherTabla(dados.items);
            animarContador($resumen, "Total de registros: " + dados.total +
                " (exibindo " + dados.items.length + ")");
            setEstado($estadoResultados, "", "");
        } catch (err) {
            $tablaBody.innerHTML = "";
            setEstado($estadoResultados, err.message, "erro");
        }
    }

    /* Anima la aparición del texto del resumen (fade + slide suave). */
    function animarContador(el, texto) {
        el.textContent = "";
        el.classList.remove("resumen-in");
        void el.offsetWidth;
        el.textContent = texto;
        el.classList.add("resumen-in");
    }

    async function exportarExcel() {
        setEstado($estadoResultados, "Gerando Excel...", "carregando");
        try {
            const resposta = await fetch(urlAdmin("exportar", {
                cargo: $filtroCargo.value,
                universidade: $filtroUniversidade.value.trim()
            }));
            if (!resposta.ok) throw new Error("Não foi possível exportar.");
            const blob = await resposta.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const disposition = resposta.headers.get("Content-Disposition") || "";
            const match = disposition.match(/filename="?([^"]+)"?/);
            a.download = match ? match[1] : "respostas.xlsx";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            setEstado($estadoResultados, "Arquivo Excel baixado.", "exito");
        } catch (err) {
            setEstado($estadoResultados, err.message, "erro");
        }
    }

    /* ---------- Controladores de eventos ---------- */

    $botonSair.addEventListener("click", function () {
        // Al salir, cerramos la sesión (no hay token en storage: recargamos).
        window.location.href = "/";
    });

    $botonFiltrar.addEventListener("click", carregarResultados);
    $botonExportar.addEventListener("click", exportarExcel);

    /* ---------- Inicialização ---------- */

    // Si el token es inválido, vacío o no se inyectó (marcador literal),
    // la API devolverá 404. Ocultamos la vista y no intentamos cargar.
    const markerSinInyectar = TOKEN && TOKEN.indexOf("__ADMIN") !== -1;
    if (!TOKEN || markerSinInyectar) {
        $resultados.hidden = true;
    } else {
        carregarResultados();
    }
})();
