"""
test_respostas.py
-----------------
Pruebas del flujo público: POST /api/respostas (creación y validación).
"""

from __future__ import annotations

import pytest


class TestCrearResposta:
    def test_crear_valida_devuelve_201(self, client, payload_valido):
        r = client.post("/api/respostas", json=payload_valido)
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True
        assert "id" in body

    def test_rechaza_inyeccion_script(self, client, payload_valido):
        payload = dict(payload_valido, nombre="<script>alert(1)</script>")
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_caracteres_control(self, client, payload_valido):
        # CRLF / control chars deben rechazarse incluso en campos de texto.
        payload = dict(payload_valido, nombre="Ana\r\nX-SPLIT")
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

        payload2 = dict(payload_valido, universidad="USP\nJunk")
        r2 = client.post("/api/respostas", json=payload2)
        assert r2.status_code == 422

    def test_rechaza_ano_especialidad_anterior_a_graduacion(
        self, client, payload_valido
    ):
        payload = dict(payload_valido, ano_graduacion=2015, ano_especialidad=2005)
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_graduacion_anterior_al_nacimiento(
        self, client, payload_valido
    ):
        payload = dict(
            payload_valido, fecha_nacimiento="2000-01-01", ano_graduacion=1999
        )
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_fiscal_no_numerico(self, client, payload_valido):
        payload = dict(payload_valido, fiscal="ABC-DEF")
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_sin_consentimiento(self, client, payload_valido):
        payload = dict(payload_valido, consentimiento=False)
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_datos_obligatorios_faltantes(self, client):
        r = client.post("/api/respostas", json={"nombre": "incompleto"})
        assert r.status_code == 422

    def test_rechaza_cargo_docente_invalido(self, client, payload_valido):
        payload = dict(payload_valido, cargo_docente="Director")
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_rechaza_fecha_futura(self, client, payload_valido):
        payload = dict(payload_valido, fecha_nacimiento="2999-01-01")
        r = client.post("/api/respostas", json=payload)
        assert r.status_code == 422

    def test_body_no_json_devuelve_422(self, client):
        r = client.post("/api/respostas", content=b"no-json", headers={
            "Content-Type": "application/json"
        })
        assert r.status_code in (400, 422)


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
