"""Pruebas del endpoint publico `GET /api/v1/votaciones/abierta` (Mision 09,
DEC-023): la papeleta que el frontend de votacion necesita para saber contra
que votacion y opciones puede votar, sin token administrativo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import _build_engine, get_db
from app.main import app
from app.models import OpcionVoto
from tests.test_habilitacion import _votacion_abierta


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


def test_get_votaciones_abierta_devuelve_papeleta_sin_token(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            votacion = _votacion_abierta(db)
            db.add(OpcionVoto(votacion_id=votacion.id, nombre="Lista A", orden=1))
            db.add(OpcionVoto(votacion_id=votacion.id, nombre="Lista B", orden=2))
            db.commit()
            votacion_id = votacion.id

        response = client.get("/api/v1/votaciones/abierta")

        assert response.status_code == 200
        body = response.json()
        assert body["votacion_id"] == votacion_id
        assert body["nombre"] == "Votacion De Prueba"
        assert [o["nombre"] for o in body["opciones"]] == ["Lista A", "Lista B"]
    finally:
        _liberar(engine)


def test_get_votaciones_abierta_404_sin_votacion_abierta(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.get("/api/v1/votaciones/abierta")
        assert response.status_code == 404
    finally:
        _liberar(engine)


def test_get_votaciones_abierta_no_expone_ningun_resultado(migrated_db_url):
    """El endpoint solo expone la papeleta (id y nombre de cada opcion), nunca
    conteos: REGLAS_NEGOCIO.md prohibe resultados antes del cierre."""
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            votacion = _votacion_abierta(db)
            db.add(OpcionVoto(votacion_id=votacion.id, nombre="Lista A", orden=1))
            db.commit()

        response = client.get("/api/v1/votaciones/abierta")

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"votacion_id", "nombre", "opciones"}
        for opcion in body["opciones"]:
            assert set(opcion.keys()) == {"id", "nombre", "orden"}
    finally:
        _liberar(engine)
