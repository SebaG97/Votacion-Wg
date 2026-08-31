"""Pruebas del endpoint `POST /api/v1/votaciones/{id}/votos` (Mision 06)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import _build_engine, get_db
from app.main import app
from tests.test_habilitacion import _matrimonio, _persona, _unidad_matrimonio, _votacion_abierta
from tests.test_voto import _opcion


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


def test_post_votos_devuelve_201_y_persiste_el_voto(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            votacion = _votacion_abierta(db)
            persona = _persona(db, "Ana", "Gomez", "0981000001")
            matrimonio = _matrimonio(db, persona)
            unidad = _unidad_matrimonio(db, matrimonio)
            opcion = _opcion(db, votacion)
            db.commit()
            votacion_id, unidad_id, opcion_id, persona_id = (
                votacion.id,
                unidad.id,
                opcion.id,
                persona.id,
            )

        response = client.post(
            f"/api/v1/votaciones/{votacion_id}/votos",
            json={
                "celular_consultado": "0981000001",
                "unidad_electoral_id": unidad_id,
                "opcion_id": opcion_id,
                "emitido_por_persona_id": persona_id,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["unidad_electoral_id"] == unidad_id
        assert body["opcion_id"] == opcion_id
        assert body["emitido_por_persona_id"] == persona_id
        assert body["celular_consultado"] == "0981000001"
        assert "id" in body
        assert "fecha_emision" in body
        assert "resultados" not in body
    finally:
        _liberar(engine)


def test_post_votos_409_si_ya_voto(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            votacion = _votacion_abierta(db)
            persona = _persona(db, "Ana", "Gomez", "0981000001")
            matrimonio = _matrimonio(db, persona)
            unidad = _unidad_matrimonio(db, matrimonio)
            opcion = _opcion(db, votacion)
            db.commit()
            votacion_id, unidad_id, opcion_id, persona_id = (
                votacion.id,
                unidad.id,
                opcion.id,
                persona.id,
            )

        payload = {
            "celular_consultado": "0981000001",
            "unidad_electoral_id": unidad_id,
            "opcion_id": opcion_id,
            "emitido_por_persona_id": persona_id,
        }
        primera = client.post(f"/api/v1/votaciones/{votacion_id}/votos", json=payload)
        assert primera.status_code == 201

        segunda = client.post(f"/api/v1/votaciones/{votacion_id}/votos", json=payload)
        assert segunda.status_code == 409
    finally:
        _liberar(engine)


def test_post_votos_409_sin_votacion_abierta(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/votaciones/9999/votos",
            json={
                "celular_consultado": "0981000001",
                "unidad_electoral_id": 1,
                "opcion_id": 1,
                "emitido_por_persona_id": 1,
            },
        )
        assert response.status_code == 409
    finally:
        _liberar(engine)
