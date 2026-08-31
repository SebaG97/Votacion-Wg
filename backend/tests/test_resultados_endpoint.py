"""Pruebas de los endpoints `GET /votaciones/{id}/resultados` y
`POST /votaciones/{id}/revelar` (Mision 08, DEC-022), incluido el control de
acceso administrativo (`require_admin`, DEC-021) sobre los dos endpoints
nuevos.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import _build_engine, get_db
from app.main import app
from app.models import Voto
from tests.test_habilitacion import _grupo, _matrimonio, _persona, _unidad_matrimonio

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


def _crear_votacion_abierta_con_opcion(client, headers):
    """Crea una votacion con una opcion y la abre via API. El voto se agrega
    despues, directo por ORM (mas rapido que pasar por `/votos`), y el
    cierre lo dispara cada prueba en el momento que necesita."""
    crear = client.post("/api/v1/votaciones", json={"nombre": "Consejo 2026"}, headers=headers)
    votacion_id = crear.json()["id"]
    opcion = client.post(
        f"/api/v1/votaciones/{votacion_id}/opciones",
        json={"nombre": "Lista A"},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/votaciones/{votacion_id}/abrir", json={"usuario": "admin@wg"}, headers=headers
    )
    return votacion_id, opcion["id"]


def test_endpoints_resultados_y_revelar_requieren_admin(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        # Sin ADMIN_API_KEY configurado: falla cerrado con 403.
        monkeypatch.setattr(settings, "admin_api_key", "")
        assert client.get("/api/v1/votaciones/1/resultados").status_code == 403
        assert client.post("/api/v1/votaciones/1/revelar").status_code == 403

        # Con ADMIN_API_KEY configurado pero sin header: 401.
        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        assert client.get("/api/v1/votaciones/1/resultados").status_code == 401
        assert client.post("/api/v1/votaciones/1/revelar").status_code == 401
    finally:
        _liberar(engine)


def test_get_resultados_bloqueado_con_votacion_abierta(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        crear = client.post(
            "/api/v1/votaciones", json={"nombre": "Consejo 2026"}, headers=_headers()
        )
        votacion_id = crear.json()["id"]
        client.post(
            f"/api/v1/votaciones/{votacion_id}/opciones",
            json={"nombre": "Lista A"},
            headers=_headers(),
        )

        # Todavia en BORRADOR.
        bloqueado_borrador = client.get(
            f"/api/v1/votaciones/{votacion_id}/resultados", headers=_headers()
        )
        assert bloqueado_borrador.status_code == 409
        assert "resultados" in bloqueado_borrador.json()["detail"].lower()

        client.post(
            f"/api/v1/votaciones/{votacion_id}/abrir",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        bloqueado_abierta = client.get(
            f"/api/v1/votaciones/{votacion_id}/resultados", headers=_headers()
        )
        assert bloqueado_abierta.status_code == 409
    finally:
        _liberar(engine)


def test_get_resultados_200_con_votacion_cerrada_y_revelar_luego(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _crear_votacion_abierta_con_opcion(client, _headers())

        with Session(bind=engine) as db:
            grupo = _grupo(db, "CIRCULO 1")
            persona = _persona(db, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
            matrimonio = _matrimonio(db, persona, grupo_id=grupo.id)
            unidad = _unidad_matrimonio(db, matrimonio)
            db.flush()
            voto = Voto(votacion_id=votacion_id, unidad_electoral_id=unidad.id, opcion_id=opcion_id)
            db.add(voto)
            db.commit()

        cerrar = client.post(
            f"/api/v1/votaciones/{votacion_id}/cerrar",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert cerrar.status_code == 200

        respuesta = client.get(
            f"/api/v1/votaciones/{votacion_id}/resultados", headers=_headers()
        )
        assert respuesta.status_code == 200
        body = respuesta.json()
        assert body["total_votos"] == 1
        assert body["totales_por_opcion"] == [
            {"opcion_id": opcion_id, "nombre": "Lista A", "votos": 1, "porcentaje": 100.0}
        ]
        assert any(
            fila["tipo"] == "MATRIMONIO_CONSAGRADO" and fila["votos_emitidos"] == 1
            for fila in body["totales_por_tipo_unidad"]
        )
        assert any(
            fila["votos_emitidos"] == 1 for fila in body["totales_por_grupo"]
        )

        revelar = client.post(
            f"/api/v1/votaciones/{votacion_id}/revelar", headers=_headers()
        )
        assert revelar.status_code == 200
        assert revelar.json()["estado"] == "RESULTADOS_REVELADOS"
        assert revelar.json()["resultados_revelados_at"] is not None

        respuesta_revelada = client.get(
            f"/api/v1/votaciones/{votacion_id}/resultados", headers=_headers()
        )
        assert respuesta_revelada.status_code == 200
        assert respuesta_revelada.json()["totales_por_opcion"] == body["totales_por_opcion"]

        revelar_de_nuevo = client.post(
            f"/api/v1/votaciones/{votacion_id}/revelar", headers=_headers()
        )
        assert revelar_de_nuevo.status_code == 409
    finally:
        _liberar(engine)


def test_post_revelar_da_409_si_la_votacion_no_esta_cerrada(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        crear = client.post(
            "/api/v1/votaciones", json={"nombre": "Consejo 2026"}, headers=_headers()
        )
        votacion_id = crear.json()["id"]

        respuesta = client.post(
            f"/api/v1/votaciones/{votacion_id}/revelar", headers=_headers()
        )
        assert respuesta.status_code == 409
    finally:
        _liberar(engine)


def test_get_resultados_formato_csv(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _crear_votacion_abierta_con_opcion(client, _headers())

        with Session(bind=engine) as db:
            grupo = _grupo(db, "CIRCULO 1")
            persona = _persona(db, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
            matrimonio = _matrimonio(db, persona, grupo_id=grupo.id)
            unidad = _unidad_matrimonio(db, matrimonio)
            db.flush()
            db.add(Voto(votacion_id=votacion_id, unidad_electoral_id=unidad.id, opcion_id=opcion_id))
            db.commit()

        client.post(
            f"/api/v1/votaciones/{votacion_id}/cerrar",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )

        respuesta = client.get(
            f"/api/v1/votaciones/{votacion_id}/resultados?formato=csv", headers=_headers()
        )

        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("text/csv")
        cuerpo = respuesta.text
        assert "total_votos,1" in cuerpo
        assert "Lista A" in cuerpo
        assert "MATRIMONIO_CONSAGRADO" in cuerpo
        assert "CIRCULO 1" in cuerpo
    finally:
        _liberar(engine)
