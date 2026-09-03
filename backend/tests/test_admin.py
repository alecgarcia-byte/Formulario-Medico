"""
test_admin.py
-------------
Pruebas del panel admin (acceso por URL/llave secreta ADMIN_TOKEN, sin login):
protección, listado, detalle (con descifrado de campos sensibles), panel HTML
y exportación Excel.
"""

from __future__ import annotations

import io

import pandas as pd

# Debe coincidir con ADMIN_TOKEN definido en conftest.py
TOKEN = "test-admin-token-12345678901234567890"


def _url(accion, token=TOKEN):
    return f"/api/admin/{token}/{accion}"


class TestProteccion:
    def test_admin_sin_token_devuelve_no_encontrado(self, client):
        # Sin token, las rutas /api/admin/<token>/... no existen -> 404.
        assert client.get("/api/admin/respostas").status_code == 404

    def test_admin_token_incorrecto_devuelve_404(self, client):
        for accion in ("respostas", "respostas/abc", "exportar"):
            r = client.get(f"/api/admin/token-incorrecto/{accion}")
            assert r.status_code == 404, accion


class TestPanelHtml:
    def test_panel_html_sin_token_devuelve_404(self, client):
        assert client.get("/admin-token-incorrecto").status_code == 404

    def test_panel_html_con_token_devuelve_html(self, client):
        r = client.get(f"/admin-{TOKEN}")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")
        body = r.text
        # El HTML no debe contener el marcador sin reemplazar.
        assert "__ADMIN_TOKEN__" not in body
        # El token real queda embebido para el JS.
        assert TOKEN in body


class TestListadoYDetalle:
    def test_listado_contiene_registro_creado(self, client, payload_valido):
        creado = client.post("/api/respostas", json=payload_valido)
        assert creado.status_code == 201
        rid = creado.json()["id"]

        lista = client.get(_url("respostas")).json()
        assert lista["total"] >= 1

        det = client.get(_url(f"respostas/{rid}"))
        assert det.status_code == 200
        item = det.json()
        # Campos sensibles descifrados:
        assert item["documento"] == payload_valido["documento"]
        assert item["fiscal"] == payload_valido["fiscal"]
        assert item["nombre"] == payload_valido["nombre"]

    def test_detalle_inexistente_devuelve_404(self, client):
        r = client.get(_url("respostas/00000000-0000-0000-0000-000000000000"))
        assert r.status_code == 404

    def test_filtro_por_cargo(self, client, payload_valido):
        client.post("/api/respostas", json=payload_valido)
        r = client.get(_url("respostas") + "?cargo=Assistente")
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["cargo_docente"] == "Assistente" for i in items)


class TestExportacion:
    def test_exportacion_descifra_y_genera_xlsx(self, client, payload_valido):
        client.post("/api/respostas", json=payload_valido)

        r = client.get(_url("exportar"))
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers["content-type"]
        assert "attachment" in r.headers["content-disposition"]

        df = pd.read_excel(io.BytesIO(r.content))
        # El documento descifrado debe aparecer en la columna correspondiente.
        columna_doc = "Documento de Identidade / Passaporte"
        assert columna_doc in df.columns
        assert payload_valido["documento"] in set(df[columna_doc])

    def test_exportacion_sin_token_devuelve_404(self, client):
        assert client.get("/api/admin/exportar").status_code == 404
