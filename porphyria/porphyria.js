/* porphyria.js - Lógica del painel admin (ruta /porphyria). */

(function () {
    "use strict";

    const API_BASE = (typeof window.FORMULARIO_API_URL === "string"
        ? window.FORMULARIO_API_URL
        : "").replace(/\/$/, "");

    const $login = document.getElementById("vista-login");
    const $resultados = document.getElementById("vista-resultados");
    const $formLogin = document.getElementById("form-login");
    const $estadoLogin = document.getElementById("estado-login");
    const $estadoResultados = document.getElementById("estado-resultados");
    const $tablaBody = document.querySelector("#tabla-resultados tbody");
    const $resumen = document.getElementById("resumen-total");
    const $botonExportar = document.getElementById("botao-exportar");
    const $botonSair = document.getElementById("botao-sair");
    const $botonFiltrar = document.getElementById("botao-filtrar");
    const $filtroCargo = document.getElementById("filtro-cargo");
    const $filtroUniversidade = document.getElementById("filtro-universidade");

    let token = sessionStorage.getItem("porphyria_token") || null;

    /* ---------- Utilitários ---------- */

    function escaparHTML(texto) {
        return String(texto == null ? "" : texto)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function setEstado(el, mensaje, tipo) {
        el.textContent = mensaje || "";
        el.className = "estado" + (tipo ? " " + tipo : "");
    }

    function mostrarVista(esResultados) {
        $login.hidden = esResultados;
        $resultados.hidden = !esResultados;
    }

    /* ---------- Autenticação ---------- */

    async function fazerLogin(usuario, senha) {
        const resposta = await fetch(API_BASE + "/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ usuario: usuario, password: senha })
        });
        if (!resposta.ok) {
            let detalle = "Credenciais inválidas.";
            try {
                const corpo = await resposta.json();
                if (corpo && corpo.detail) detalle = corpo.detail;
            } catch (_) { /* ignorar */ }
            throw new Error(detalle);
        }
        return (await resposta.json()).access_token;
    }

    /* ---------- Liste e exportação ---------- */

    async function listarRespostas(filtros) {
        const params = new URLSearchParams();
        if (filtros && filtros.cargo) params.set("cargo", filtros.cargo);
        if (filtros && filtros.universidade) params.set("universidade", filtros.universidade);
        const resposta = await fetch(API_BASE + "/api/admin/respostas?" + params.toString(), {
            headers: { "Authorization": "Bearer " + token }
        });
        if (resposta.status === 401) {
            token = null;
            sessionStorage.removeItem("porphyria_token");
            throw new Error("Sessão expirada. Faça login novamente.");
        }
        if (!resposta.ok) {
            throw new Error("Não foi possível carregar os resultados.");
        }
        return await resposta.json();
    }

    function preencherTabla(items) {
        $tablaBody.innerHTML = "";
        if (!items || items.length === 0) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 7;
            td.textContent = "Nenhum resultado encontrado.";
            td.style.textAlign = "center";
            tr.appendChild(td);
            $tablaBody.appendChild(tr);
            return;
        }
        items.forEach(function (item) {
            const tr = document.createElement("tr");
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
        setEstado($estadoResultados, "Carregando resultados...", "carregando");
        try {
            const dados = await listarRespostas({
                cargo: $filtroCargo.value,
                universidade: $filtroUniversidade.value.trim()
            });
            preencherTabla(dados.items);
            $resumen.textContent = "Total de registros: " + dados.total +
                " (exibindo " + dados.items.length + ")";
            setEstado($estadoResultados, "", "");
        } catch (err) {
            setEstado($estadoResultados, err.message, "erro");
        }
    }

    async function exportarExcel() {
        setEstado($estadoResultados, "Gerando Excel...", "carregando");
        try {
            const params = new URLSearchParams();
            if ($filtroCargo.value) params.set("cargo", $filtroCargo.value);
            if ($filtroUniversidade.value.trim()) {
                params.set("universidade", $filtroUniversidade.value.trim());
            }
            const resposta = await fetch(API_BASE + "/api/admin/exportar?" + params.toString(), {
                headers: { "Authorization": "Bearer " + token }
            });
            if (resposta.status === 401) {
                token = null;
                sessionStorage.removeItem("porphyria_token");
                throw new Error("Sessão expirada. Faça login novamente.");
            }
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

    $formLogin.addEventListener("submit", async function (e) {
        e.preventDefault();
        const usuario = document.getElementById("usuario").value.trim();
        const senha = document.getElementById("password").value;
        if (!usuario || !senha) {
            setEstado($estadoLogin, "Preencha usuário e senha.", "erro");
            return;
        }
        setEstado($estadoLogin, "Autenticando...", "carregando");
        document.getElementById("botao-login").disabled = true;
        try {
            token = await fazerLogin(usuario, senha);
            sessionStorage.setItem("porphyria_token", token);
            mostrarVista(true);
            carregarResultados();
        } catch (err) {
            setEstado($estadoLogin, err.message, "erro");
        } finally {
            document.getElementById("botao-login").disabled = false;
        }
    });

    $botonSair.addEventListener("click", function () {
        token = null;
        sessionStorage.removeItem("porphyria_token");
        mostrarVista(false);
        setEstado($estadoLogin, "", "");
        document.getElementById("usuario").value = "";
        document.getElementById("password").value = "";
    });

    $botonFiltrar.addEventListener("click", carregarResultados);
    $botonExportar.addEventListener("click", exportarExcel);

    /* ---------- Initial check ---------- */

    if (token) {
        mostrarVista(true);
        carregarResultados();
    } else {
        mostrarVista(false);
    }
})();
