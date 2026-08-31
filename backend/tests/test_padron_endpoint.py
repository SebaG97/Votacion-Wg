"""Pruebas del endpoint `POST /api/v1/padron/importaciones` (Mision 04)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import _build_engine, get_db
from app.main import app
from tests.test_importador_padron import _construir_excel_fixture


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


def test_post_importaciones_padron_devuelve_resumen(migrated_db_url, tmp_path):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        ruta = tmp_path / "fixture.xlsx"
        _construir_excel_fixture(ruta)

        response = client.post(
            "/api/v1/padron/importaciones",
            json={"excel_path": str(ruta), "usuario": "tester"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["estado"] == "COMPLETADA"
        assert body["usuario"] == "tester"
        assert body["resumen"]["personas"]["total"] == 8
        assert body["resumen"]["matrimonios"]["total"] == 5
    finally:
        _liberar(engine)


def test_post_importaciones_padron_404_si_no_existe_el_excel(migrated_db_url, tmp_path):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/padron/importaciones",
            json={"excel_path": str(tmp_path / "no_existe.xlsx")},
        )
        assert response.status_code == 404
    finally:
        _liberar(engine)


def test_post_importaciones_padron_409_si_hay_votacion_abierta(migrated_db_url, tmp_path):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        ruta = tmp_path / "fixture.xlsx"
        _construir_excel_fixture(ruta)

        primera = client.post("/api/v1/padron/importaciones", json={"excel_path": str(ruta)})
        assert primera.status_code == 201

        with Session(bind=engine) as db:
            from app.models import Votacion
            from app.models.enums import EstadoVotacion

            db.add(Votacion(nombre="Votacion En Curso", estado=EstadoVotacion.ABIERTA))
            db.commit()

        segunda = client.post("/api/v1/padron/importaciones", json={"excel_path": str(ruta)})
        assert segunda.status_code == 409
    finally:
        _liberar(engine)
