"""
test_admin.py
-------------
Pruebas del panel admin (acceso por URL permitida con token JWT de acceso
único): protección, listado, detalle (con descifrado de campos sensibles),
panel HTML, exportación Excel y revocación de acceso.
"""

from __future__ import annotations

import io

import pandas as pd

from backend.utils.security import verify_jwt


def _url(accion, token):
    return f"/api/admin/{token}/{accion}"


class TestProteccion:
    def test_admin_sin_token_devuelve_no_encontrado(self, client):
        # Sin token, las rutas /api/admin/<token>/... no existen -> 404.
        assert client.get("/api/admin/respostas").status_code == 404

    def test_admin_token_invalido_devuelve_404(self, client):
        # Un token que no es un JWT de acceso válido -> 404.
        for accion in ("respostas", "respostas/abc", "exportar"):
            r = client.get(_url("token-incorrecto-123", accion))
            assert r.status_code == 404, accion

    def test_admin_con_token_falsificado_devuelve_404(self, client):
        # Un JWT malformado (que no se puede verificar) -> 404.
        r = client.get("/admin-abc.def.ghi")
        assert r.status_code == 404


class TestPanelHtml:
    def test_panel_html_sin_token_devuelve_404(self, client):
        assert client.get("/admin-token-incorrecto").status_code == 404

    def test_panel_html_con_token_devuelve_html(self, client, token_admin):
        r = client.get(f"/admin-{token_admin}")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")
        body = r.text
        # El HTML no debe contener el marcador sin reemplazar.
        assert "__ADMIN_TOKEN__" not in body
        # El JWT de acceso queda embebido para el JS.
        assert token_admin in body


class TestListadoYDetalle:
    def test_listado_contiene_registro_creado(
        self, client, payload_valido, token_admin
    ):
        creado = client.post("/api/respostas", json=payload_valido)
        assert creado.status_code == 201
        rid = creado.json()["id"]

        lista = client.get(_url("respostas", token_admin)).json()
        assert lista["total"] >= 1

        det = client.get(_url(f"respostas/{rid}", token_admin))
        assert det.status_code == 200
        item = det.json()
        # Campos sensibles descifrados:
        assert item["documento"] == payload_valido["documento"]
        assert item["fiscal"] == payload_valido["fiscal"]
        assert item["nombre"] == payload_valido["nombre"]

    def test_detalle_inexistente_devuelve_404(self, client, token_admin):
        r = client.get(
            _url("respostas/00000000-0000-0000-0000-000000000000", token_admin)
        )
        assert r.status_code == 404

    def test_filtro_por_cargo(
        self, client, payload_valido, token_admin
    ):
        client.post("/api/respostas", json=payload_valido)
        r = client.get(_url("respostas", token_admin) + "?cargo=Assistente")
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["cargo_docente"] == "Assistente" for i in items)


class TestExportacion:
    def test_exportacion_descifra_y_genera_xlsx(
        self, client, payload_valido, token_admin
    ):
        client.post("/api/respostas", json=payload_valido)

        r = client.get(_url("exportar", token_admin))
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


class TestRevocacion:
    def test_jwt_revocado_devuelve_404(self, client, token_admin):
        # Revocamos la sesión (jti) asociada al token de acceso.
        from backend import models
        from backend.database import SessionLocal

        payload = verify_jwt(token_admin)
        assert payload is not None and payload.get("jti")
        jti = payload["jti"]

        with SessionLocal() as db:
            from sqlalchemy import select

            sesion = db.scalar(
                select(models.AdminSession).where(
                    models.AdminSession.token_jti == jti
                )
            )
            assert sesion is not None
            sesion.revocado = True
            db.commit()

        # Tras revocar, el acceso a la API y al panel devuelve 404.
        r = client.get(_url("respostas", token_admin))
        assert r.status_code == 404
        r = client.get(f"/admin-{token_admin}")
        assert r.status_code == 404