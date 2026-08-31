"""Pruebas de los endpoints de administracion de votacion (Mision 07):
crear, cargar opciones, abrir, cerrar, estado operativo, y el control de
acceso administrativo (`require_admin`, DEC-021).
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import _build_engine, get_db
from app.main import app
from tests.test_habilitacion import _matrimonio, _persona, _unidad_matrimonio, _votacion_abierta

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


def test_crear_votacion_devuelve_201_en_borrador(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/votaciones", json={"nombre": "Consejo 2026"}, headers=_headers()
        )

        assert response.status_code == 201
        body = response.json()
        assert body["estado"] == "BORRADOR"
        assert body["abierta_por"] is None
        votacion_id = body["id"]

        opcion_response = client.post(
            f"/api/v1/votaciones/{votacion_id}/opciones",
            json={"nombre": "Lista A"},
            headers=_headers(),
        )
        assert opcion_response.status_code == 201
        assert opcion_response.json()["votacion_id"] == votacion_id
    finally:
        _liberar(engine)


def test_abrir_sin_opciones_da_409(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        crear = client.post(
            "/api/v1/votaciones", json={"nombre": "Consejo 2026"}, headers=_headers()
        )
        votacion_id = crear.json()["id"]

        response = client.post(
            f"/api/v1/votaciones/{votacion_id}/abrir",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert response.status_code == 409
    finally:
        _liberar(engine)


def test_abrir_y_cerrar_ciclo_completo(migrated_db_url, monkeypatch):
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

        abrir = client.post(
            f"/api/v1/votaciones/{votacion_id}/abrir",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert abrir.status_code == 200
        assert abrir.json()["estado"] == "ABIERTA"
        assert abrir.json()["abierta_por"] == "admin@wg"

        segunda = client.post(
            "/api/v1/votaciones", json={"nombre": "Otra Votacion"}, headers=_headers()
        )
        segunda_id = segunda.json()["id"]
        client.post(
            f"/api/v1/votaciones/{segunda_id}/opciones",
            json={"nombre": "Lista B"},
            headers=_headers(),
        )
        abrir_segunda = client.post(
            f"/api/v1/votaciones/{segunda_id}/abrir",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert abrir_segunda.status_code == 409

        cerrar = client.post(
            f"/api/v1/votaciones/{votacion_id}/cerrar",
            json={"usuario": "otro-admin@wg"},
            headers=_headers(),
        )
        assert cerrar.status_code == 200
        assert cerrar.json()["estado"] == "CERRADA"
        assert cerrar.json()["cerrada_por"] == "otro-admin@wg"

        cerrar_otra_vez = client.post(
            f"/api/v1/votaciones/{votacion_id}/cerrar",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )
        assert cerrar_otra_vez.status_code == 409
    finally:
        _liberar(engine)


def test_get_estado_no_expone_nada_por_opcion(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        with Session(bind=engine) as db:
            votacion = _votacion_abierta(db)
            persona = _persona(db, "Ana", "Gomez", "0981000001")
            matrimonio = _matrimonio(db, persona)
            _unidad_matrimonio(db, matrimonio)
            db.commit()
            votacion_id = votacion.id

        response = client.get(f"/api/v1/votaciones/{votacion_id}/estado", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        assert body["votacion_id"] == votacion_id
        assert body["unidades_por_estado"]["habilitada"] == 1
        assert body["votos_emitidos"] == 0
        assert body["pendientes"] == 1
        assert "opcion_id" not in body
        cuerpo_serializado = str(body).lower()
        assert "opcion" not in cuerpo_serializado
    finally:
        _liberar(engine)


def test_endpoints_administrativos_sin_token_dan_401_o_403(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        # Sin ADMIN_API_KEY configurado: falla cerrado con 403, nunca abierto.
        monkeypatch.setattr(settings, "admin_api_key", "")
        sin_configurar = client.post("/api/v1/votaciones", json={"nombre": "X"})
        assert sin_configurar.status_code == 403

        # Con ADMIN_API_KEY configurado pero sin header: 401.
        monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
        sin_header = client.post("/api/v1/votaciones", json={"nombre": "X"})
        assert sin_header.status_code == 401

        # Con header incorrecto: 401.
        con_token_incorrecto = client.post(
            "/api/v1/votaciones",
            json={"nombre": "X"},
            headers={"X-Admin-Token": "incorrecto"},
        )
        assert con_token_incorrecto.status_code == 401

        # Con el token correcto: pasa el control de acceso.
        con_token_correcto = client.post(
            "/api/v1/votaciones", json={"nombre": "X"}, headers=_headers()
        )
        assert con_token_correcto.status_code == 201
    finally:
        _liberar(engine)


def test_votos_y_habilitaciones_consultar_siguen_sin_proteccion(migrated_db_url, monkeypatch):
    """DEC-020 documenta que `POST /votaciones/{id}/votos` y
    `POST /habilitaciones/consultar` quedan sin control de acceso a proposito
    -- esta mision agrega `require_admin` solo a los endpoints
    administrativos, y esta prueba confirma que esos dos no quedaron
    protegidos por accidente al conectar el router nuevo."""
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        habilitaciones_sin_token = client.post(
            "/api/v1/habilitaciones/consultar", json={"celular": "0981000001"}
        )
        assert habilitaciones_sin_token.status_code != 401
        assert habilitaciones_sin_token.status_code != 403

        votos_sin_token = client.post(
            "/api/v1/votaciones/9999/votos",
            json={
                "celular_consultado": "0981000001",
                "unidad_electoral_id": 1,
                "opcion_id": 1,
                "emitido_por_persona_id": 1,
            },
        )
        assert votos_sin_token.status_code != 401
        assert votos_sin_token.status_code != 403
    finally:
        _liberar(engine)
