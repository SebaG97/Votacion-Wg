"""Pruebas del endpoint `POST /api/v1/habilitaciones/consultar` (Mision 05)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import _build_engine, get_db
from app.main import app
from tests.test_habilitacion import _grupo, _matrimonio, _persona, _unidad_matrimonio, _votacion_abierta


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


def test_post_habilitaciones_consultar_devuelve_unidad_disponible(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            _votacion_abierta(db)
            grupo = _grupo(db, "CIRCULO 1")
            persona = _persona(db, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
            matrimonio = _matrimonio(db, persona, grupo_id=grupo.id)
            _unidad_matrimonio(db, matrimonio)
            db.commit()

        response = client.post(
            "/api/v1/habilitaciones/consultar", json={"celular": "0981000001"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["habilitado"] is True
        assert len(body["unidades"]) == 1
        assert body["unidades"][0]["disponible"] is True
    finally:
        _liberar(engine)


def test_post_habilitaciones_consultar_409_sin_votacion_abierta(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/habilitaciones/consultar", json={"celular": "0981000001"}
        )
        assert response.status_code == 409
    finally:
        _liberar(engine)
