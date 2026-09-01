"""Pruebas del rate limiting por IP (DEC-029) sobre los dos endpoints
operativos sin control de acceso: `POST /habilitaciones/consultar` y
`POST /votaciones/{id}/votos` (DEC-020). No reemplaza autenticacion real por
votante; solo eleva el costo de escanear el padron o automatizar intentos de
voto durante los dias/semanas que la votacion queda abierta en internet.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import _build_engine, get_db
from app.main import app


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


def test_habilitaciones_consultar_devuelve_429_al_superar_el_limite_por_ip(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        limite = settings.rate_limit_por_minuto
        for _ in range(limite):
            response = client.post(
                "/api/v1/habilitaciones/consultar", json={"celular": "0981000001"}
            )
            assert response.status_code != 429

        excedida = client.post(
            "/api/v1/habilitaciones/consultar", json={"celular": "0981000001"}
        )
        assert excedida.status_code == 429
    finally:
        limiter.reset()
        _liberar(engine)


def test_votos_devuelve_429_al_superar_el_limite_por_ip(migrated_db_url):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        limite = settings.rate_limit_por_minuto
        payload = {
            "celular_consultado": "0981000001",
            "unidad_electoral_id": 1,
            "opcion_id": 1,
            "emitido_por_persona_id": 1,
        }
        for _ in range(limite):
            response = client.post("/api/v1/votaciones/9999/votos", json=payload)
            assert response.status_code != 429

        excedida = client.post("/api/v1/votaciones/9999/votos", json=payload)
        assert excedida.status_code == 429
    finally:
        limiter.reset()
        _liberar(engine)


def test_rate_limit_es_por_ip_no_global(migrated_db_url):
    """Dos `TestClient` distintos comparten proceso (y por lo tanto el mismo
    `Limiter`), pero `get_remote_address` distingue por IP de origen: en un
    despliegue real, un votante no debe verse afectado por el rate limit que
    consumio otro votante desde otra IP. Con `TestClient`, ambos clientes
    comparten la misma IP simulada (`testclient`), asi que esta prueba
    documenta el comportamiento esperado usando `X-Forwarded-For` para
    simular dos origenes distintos -- sin este header, `get_remote_address`
    usa `request.client.host`, igual para ambos clientes de prueba."""
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        limite = settings.rate_limit_por_minuto
        for _ in range(limite):
            response = client.post(
                "/api/v1/habilitaciones/consultar",
                json={"celular": "0981000001"},
                headers={"X-Forwarded-For": "10.0.0.1"},
            )
            assert response.status_code != 429

        # Otra IP simulada: no deberia estar afectada por el consumo de la anterior.
        otra_ip = client.post(
            "/api/v1/habilitaciones/consultar",
            json={"celular": "0981000001"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert otra_ip.status_code != 429
    finally:
        limiter.reset()
        _liberar(engine)
