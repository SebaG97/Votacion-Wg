"""Pruebas del endpoint `POST /api/v1/padron/importaciones` (Mision 04),
protegido por `require_admin` desde la Mision 10 (DEC-025)."""

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


def test_post_importaciones_padron_devuelve_resumen(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        ruta = tmp_path / "fixture.xlsx"
        _construir_excel_fixture(ruta)

        response = client.post(
            "/api/v1/padron/importaciones",
            json={"excel_path": str(ruta), "usuario": "tester"},
            headers=_headers(),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["estado"] == "COMPLETADA"
        assert body["usuario"] == "tester"
        assert body["resumen"]["personas"]["total"] == 8
        assert body["resumen"]["matrimonios"]["total"] == 5
    finally:
        _liberar(engine)


def test_post_importaciones_padron_404_si_no_existe_el_excel(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/padron/importaciones",
            json={"excel_path": str(tmp_path / "no_existe.xlsx")},
            headers=_headers(),
        )
        assert response.status_code == 404
    finally:
        _liberar(engine)


def test_post_importaciones_padron_409_si_hay_votacion_abierta(migrated_db_url, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        ruta = tmp_path / "fixture.xlsx"
        _construir_excel_fixture(ruta)

        primera = client.post(
            "/api/v1/padron/importaciones", json={"excel_path": str(ruta)}, headers=_headers()
        )
        assert primera.status_code == 201

        with Session(bind=engine) as db:
            from app.models import Votacion
            from app.models.enums import EstadoVotacion

            db.add(Votacion(nombre="Votacion En Curso", estado=EstadoVotacion.ABIERTA))
            db.commit()

        segunda = client.post(
            "/api/v1/padron/importaciones", json={"excel_path": str(ruta)}, headers=_headers()
        )
        assert segunda.status_code == 409
    finally:
        _liberar(engine)


def test_post_importaciones_padron_sin_token_da_401_o_403(migrated_db_url, tmp_path, monkeypatch):
    """DEC-025: `POST /padron/importaciones` puede reimportar/recrear todo el
    padron y hasta esta mision no tenia ningun control de acceso -- un olvido
    corregido aca, con el mismo comportamiento de `require_admin` que el resto
    del panel administrativo (DEC-021)."""
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        monkeypatch.setattr(settings, "admin_api_key", "")
        sin_configurar = client.post("/api/v1/padron/importaciones", json={})
        assert sin_configurar.status_code == 403

        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        sin_header = client.post("/api/v1/padron/importaciones", json={})
        assert sin_header.status_code == 401
    finally:
        _liberar(engine)
