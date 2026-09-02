"""Pruebas de los endpoints administrativos de padron agregados en la
Mision 10 (DEC-025): historial de importaciones, listado filtrable de
incidencias y marcarlas como revisadas. Mision 12 (DEC-031) agrega el visor
de padron filtrable y paginado (`GET /padron/personas`)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import _build_engine, get_db
from app.main import app
from tests.test_importador_padron import _construir_excel_fixture

ADMIN_TOKEN = "test-admin-token"


def _cliente_con_db(migrated_db_url):
    engine = _build_engine(migrated_db_url)

    def override_get_db():
        db = Session(bind=engine)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), engine


def _liberar(engine):
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def _headers() -> dict[str, str]:
    return {"X-Admin-Token": ADMIN_TOKEN}


def _importar(client, tmp_path):
    ruta = tmp_path / "fixture.xlsx"
    _construir_excel_fixture(ruta)
    response = client.post(
        "/api/v1/padron/importaciones",
        json={"excel_path": str(ruta), "usuario": "tester"},
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()


def test_get_importaciones_devuelve_historial_mas_nueva_primero(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        primera = _importar(client, tmp_path)
        segunda = _importar(client, tmp_path)

        response = client.get("/api/v1/padron/importaciones", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["id"] == segunda["id"]
        assert body[1]["id"] == primera["id"]
    finally:
        _liberar(engine)


def test_get_importaciones_sin_token_da_401_o_403(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        monkeypatch.setattr(settings, "admin_api_key", "")
        assert client.get("/api/v1/padron/importaciones").status_code == 403

        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        assert client.get("/api/v1/padron/importaciones").status_code == 401
    finally:
        _liberar(engine)


def test_get_incidencias_lista_y_filtra_por_severidad_tipo_y_resuelta(
    migrated_db_url, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        todas = client.get("/api/v1/padron/incidencias", headers=_headers())
        assert todas.status_code == 200
        cuerpo = todas.json()
        assert len(cuerpo) > 0
        primera_incidencia = cuerpo[0]
        assert primera_incidencia["resuelto_por"] is None
        assert primera_incidencia["resuelto_at"] is None

        por_severidad = client.get(
            "/api/v1/padron/incidencias",
            params={"severidad": primera_incidencia["severidad"]},
            headers=_headers(),
        )
        assert por_severidad.status_code == 200
        assert all(i["severidad"] == primera_incidencia["severidad"] for i in por_severidad.json())

        por_tipo = client.get(
            "/api/v1/padron/incidencias",
            params={"tipo": primera_incidencia["tipo"]},
            headers=_headers(),
        )
        assert por_tipo.status_code == 200
        assert all(i["tipo"] == primera_incidencia["tipo"] for i in por_tipo.json())

        no_resueltas = client.get(
            "/api/v1/padron/incidencias", params={"resuelta": False}, headers=_headers()
        )
        assert no_resueltas.status_code == 200
        assert len(no_resueltas.json()) == len(cuerpo)

        resueltas = client.get(
            "/api/v1/padron/incidencias", params={"resuelta": True}, headers=_headers()
        )
        assert resueltas.status_code == 200
        assert resueltas.json() == []
    finally:
        _liberar(engine)


def test_post_resolver_incidencia_marca_resuelto_por_y_at_sin_tocar_unidades(
    migrated_db_url, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)
        incidencia_id = client.get("/api/v1/padron/incidencias", headers=_headers()).json()[0]["id"]

        with Session(bind=engine) as db:
            from app.models import UnidadElectoral

            estados_antes = sorted(
                (u.id, u.estado) for u in db.query(UnidadElectoral).all()
            )

        response = client.post(
            f"/api/v1/padron/incidencias/{incidencia_id}/resolver",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["resuelto_por"] == "admin@wg"
        assert body["resuelto_at"] is not None

        with Session(bind=engine) as db:
            from app.models import UnidadElectoral

            estados_despues = sorted(
                (u.id, u.estado) for u in db.query(UnidadElectoral).all()
            )
        assert estados_antes == estados_despues

        otra_vez = client.post(
            f"/api/v1/padron/incidencias/{incidencia_id}/resolver",
            json={"usuario": "otro-admin@wg"},
            headers=_headers(),
        )
        assert otra_vez.status_code == 409

        resueltas = client.get(
            "/api/v1/padron/incidencias", params={"resuelta": True}, headers=_headers()
        )
        assert len(resueltas.json()) == 1
        assert resueltas.json()[0]["id"] == incidencia_id
    finally:
        _liberar(engine)


def test_post_resolver_incidencia_inexistente_da_404(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/padron/incidencias/9999/resolver",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert response.status_code == 404
    finally:
        _liberar(engine)


def test_get_incidencias_sin_token_da_401_o_403(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        monkeypatch.setattr(settings, "admin_api_key", "")
        assert client.get("/api/v1/padron/incidencias").status_code == 403

        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        assert client.get("/api/v1/padron/incidencias").status_code == 401
    finally:
        _liberar(engine)


# --- GET /padron/personas (Mision 12, DEC-031): visor de padron filtrable y
# paginado. El fixture de `_construir_excel_fixture` (test_importador_padron.py)
# tiene 8 personas conocidas: Pereira Juan / Fernandez Maria (CIRCULO A,
# comparten celular "0981-111-111" -> "0981111111", CI de Juan "1234567"),
# Gonzalez Pedro (CIRCULO B), Diaz Roberto / Diaz Insfran Sonia (CIRCULO D),
# Benitez Marcos / Benitez Rojas Laura (CIRCULO E), Lopez Ana (POSTULANTES B).


def test_get_padron_personas_lista_todas_con_paginacion_por_defecto(
    migrated_db_url, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get("/api/v1/padron/personas", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 8
        assert body["pagina"] == 1
        assert body["tamanio_pagina"] == 50
        assert len(body["items"]) == 8
        # Deliberadamente sin ningun dato de voto (DEC-031).
        assert "voto" not in str(body).lower()
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_circulo(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas", params={"circulo": "CIRCULO A"}, headers=_headers()
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert {item["apellidos"] for item in body["items"]} == {"Pereira", "Fernandez"}
        assert all(item["circulo"] == "CIRCULO A" for item in body["items"])
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_nombre(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas", params={"nombre": "pereira"}, headers=_headers()
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["nombres"] == "Juan"
        assert body["items"][0]["apellidos"] == "Pereira"
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_documento(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas", params={"documento": "1234567"}, headers=_headers()
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["documento"] == "1234567"
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_celular(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas", params={"celular": "0981111111"}, headers=_headers()
        )

        assert response.status_code == 200
        body = response.json()
        # Pereira Juan y Fernandez Maria comparten el mismo celular (DEC-008).
        assert body["total"] == 2
        assert all(item["celular"] == "0981111111" for item in body["items"])
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_estado_persona(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas", params={"estado_persona": "ACTIVA"}, headers=_headers()
        )

        assert response.status_code == 200
        body = response.json()
        # Ninguna persona de este fixture tiene marca de baja.
        assert body["total"] == 8
        assert all(item["estado"] == "ACTIVA" for item in body["items"])
    finally:
        _liberar(engine)


def test_get_padron_personas_filtra_por_estado_y_tipo_de_unidad_electoral(
    migrated_db_url, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        todos = client.get("/api/v1/padron/personas", headers=_headers()).json()["items"]
        alguna_unidad = next(
            u for item in todos for u in item["unidades_electorales"] if u["estado"]
        )

        response = client.get(
            "/api/v1/padron/personas",
            params={
                "estado_unidad_electoral": alguna_unidad["estado"],
                "tipo_unidad_electoral": alguna_unidad["tipo"],
            },
            headers=_headers(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        for item in body["items"]:
            assert any(
                u["estado"] == alguna_unidad["estado"] and u["tipo"] == alguna_unidad["tipo"]
                for u in item["unidades_electorales"]
            )
    finally:
        _liberar(engine)


def test_get_padron_personas_combina_filtros(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        response = client.get(
            "/api/v1/padron/personas",
            params={"circulo": "CIRCULO A", "estado_persona": "ACTIVA"},
            headers=_headers(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2

        sin_match = client.get(
            "/api/v1/padron/personas",
            params={"circulo": "CIRCULO A", "documento": "no-existe"},
            headers=_headers(),
        )
        assert sin_match.status_code == 200
        assert sin_match.json()["total"] == 0
    finally:
        _liberar(engine)


def test_get_padron_personas_pagina(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        _importar(client, tmp_path)

        pagina1 = client.get(
            "/api/v1/padron/personas",
            params={"tamanio_pagina": 3, "pagina": 1},
            headers=_headers(),
        ).json()
        pagina3 = client.get(
            "/api/v1/padron/personas",
            params={"tamanio_pagina": 3, "pagina": 3},
            headers=_headers(),
        ).json()

        assert pagina1["total"] == 8
        assert len(pagina1["items"]) == 3
        assert len(pagina3["items"]) == 2  # 8 = 3 + 3 + 2

        ids_pagina1 = {item["id"] for item in pagina1["items"]}
        ids_pagina3 = {item["id"] for item in pagina3["items"]}
        assert ids_pagina1.isdisjoint(ids_pagina3)
    finally:
        _liberar(engine)


def test_get_padron_personas_sin_token_da_401_o_403(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        monkeypatch.setattr(settings, "admin_api_key", "")
        assert client.get("/api/v1/padron/personas").status_code == 403

        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        assert client.get("/api/v1/padron/personas").status_code == 401
    finally:
        _liberar(engine)
