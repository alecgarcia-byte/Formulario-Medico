"""
test_admin.py
-------------
Pruebas del panel admin: autenticación JWT, protección, listado, detalle
(con descifrado de campos sensibles) y exportación Excel.
"""

from __future__ import annotations

import io

import pandas as pd


class TestProteccion:
    def test_admin_sin_token_devuelve_401(self, client):
        for ruta in ("/api/admin/respostas", "/api/admin/exportar"):
            r = client.get(ruta)
            assert r.status_code == 401, ruta

    def test_detalle_sin_token_devuelve_401(self, client):
        assert client.get("/api/admin/respostas/abc").status_code == 401

    def test_login_incorrecto_devuelve_401(self, client):
        r = client.post(
            "/api/admin/login",
            json={"usuario": "admin", "password": "password-erronea"},
        )
        assert r.status_code == 401

    def test_token_invalido_devuelve_401(self, client):
        r = client.get(
            "/api/admin/respostas",
            headers={"Authorization": "Bearer token-invalido"},
        )
        assert r.status_code == 401


class TestLogin:
    def test_login_correcto_devuelve_token(self, client, password_admin):
        r = client.post(
            "/api/admin/login",
            json={"usuario": "admin", "password": password_admin},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0


class TestListadoYDetalle:
    def test_listado_contiene_registro_creado(self, client, payload_valido):
        creado = client.post("/api/respostas", json=payload_valido)
        assert creado.status_code == 201
        rid = creado.json()["id"]

        r = client.post("/api/admin/login",
                        json={"usuario": "admin", "password": "super-secreto"})
        token = r.json()["access_token"]

        lista = client.get(
            "/api/admin/respostas",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert lista["total"] >= 1

        det = client.get(
            f"/api/admin/respostas/{rid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert det.status_code == 200
        item = det.json()
        # Campos sensibles descifrados:
        assert item["documento"] == payload_valido["documento"]
        assert item["fiscal"] == payload_valido["fiscal"]
        assert item["nombre"] == payload_valido["nombre"]

    def test_detalle_inexistente_devuelve_404(self, client):
        token = client.post("/api/admin/login",
                            json={"usuario": "admin",
                                  "password": "super-secreto"}).json()["access_token"]
        r = client.get(
            "/api/admin/respostas/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_filtro_por_cargo(self, client, payload_valido):
        client.post("/api/respostas", json=payload_valido)
        token = client.post("/api/admin/login",
                            json={"usuario": "admin",
                                  "password": "super-secreto"}).json()["access_token"]
        r = client.get(
            "/api/admin/respostas?cargo=Assistente",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["cargo_docente"] == "Assistente" for i in items)


class TestExportacion:
    def test_exportacion_descifra_y_genera_xlsx(self, client, payload_valido):
        client.post("/api/respostas", json=payload_valido)
        token = client.post("/api/admin/login",
                            json={"usuario": "admin",
                                  "password": "super-secreto"}).json()["access_token"]

        r = client.get(
            "/api/admin/exportar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers["content-type"]
        assert "attachment" in r.headers["content-disposition"]

        df = pd.read_excel(io.BytesIO(r.content))
        # El documento descifrado debe aparecer en la columna correspondiente.
        columna_doc = "Documento de Identidade / Passaporte"
        assert columna_doc in df.columns
        assert payload_valido["documento"] in set(df[columna_doc])

    def test_exportacion_sin_token_devuelve_401(self, client):
        assert client.get("/api/admin/exportar").status_code == 401
