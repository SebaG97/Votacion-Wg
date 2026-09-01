"""Pruebas de los endpoints administrativos de padron agregados en la
Mision 10 (DEC-025): historial de importaciones, listado filtrable de
incidencias y marcarlas como revisadas."""

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
