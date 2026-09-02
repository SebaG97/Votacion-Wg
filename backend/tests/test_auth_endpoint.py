"""Pruebas de `POST /api/v1/auth/login` (Mision 12, DEC-030): login
administrativo usuario/contrasena que devuelve el mismo `ADMIN_API_KEY` que
ya usa `require_admin` (DEC-021), sin tocar ese mecanismo. Cubre credenciales
correctas, incorrectas, variables de entorno sin configurar (falla cerrado) y
el limite de intentos por IP (`RATE_LIMIT_LOGIN`, `app/core/rate_limit.py`)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import _build_engine, get_db
from app.main import app

ADMIN_TOKEN = "test-admin-token"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "votacion2026"


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


def _configurar_credenciales(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    monkeypatch.setattr(settings, "admin_username", ADMIN_USERNAME)
    monkeypatch.setattr(settings, "admin_password", ADMIN_PASSWORD)


def test_login_con_credenciales_correctas_devuelve_el_admin_api_key(
    migrated_db_url, monkeypatch
):
    _configurar_credenciales(monkeypatch)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"usuario": ADMIN_USERNAME, "contrasena": ADMIN_PASSWORD},
        )
        assert response.status_code == 200
        assert response.json() == {"token": ADMIN_TOKEN}

        # El token devuelto es exactamente el que exige `require_admin`.
        protegida = client.get(
            "/api/v1/padron/importaciones", headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        assert protegida.status_code == 200
    finally:
        _liberar(engine)


def test_login_con_usuario_incorrecto_da_401(migrated_db_url, monkeypatch):
    _configurar_credenciales(monkeypatch)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"usuario": "otro-usuario", "contrasena": ADMIN_PASSWORD},
        )
        assert response.status_code == 401
    finally:
        _liberar(engine)


def test_login_con_contrasena_incorrecta_da_401(migrated_db_url, monkeypatch):
    _configurar_credenciales(monkeypatch)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"usuario": ADMIN_USERNAME, "contrasena": "incorrecta"},
        )
        assert response.status_code == 401
    finally:
        _liberar(engine)


def test_login_sin_variables_de_entorno_configuradas_da_403(migrated_db_url, monkeypatch):
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        monkeypatch.setattr(settings, "admin_api_key", "")
        monkeypatch.setattr(settings, "admin_username", "")
        monkeypatch.setattr(settings, "admin_password", "")
        response = client.post(
            "/api/v1/auth/login", json={"usuario": "admin", "contrasena": "cualquiera"}
        )
        assert response.status_code == 403

        # Falla cerrado tambien si solo falta una de las tres variables.
        monkeypatch.setattr(settings, "admin_username", ADMIN_USERNAME)
        monkeypatch.setattr(settings, "admin_password", ADMIN_PASSWORD)
        # admin_api_key sigue vacio.
        response_parcial = client.post(
            "/api/v1/auth/login",
            json={"usuario": ADMIN_USERNAME, "contrasena": ADMIN_PASSWORD},
        )
        assert response_parcial.status_code == 403
    finally:
        _liberar(engine)


def test_login_dispara_429_al_superar_el_limite_de_intentos_por_ip(
    migrated_db_url, monkeypatch
):
    _configurar_credenciales(monkeypatch)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"usuario": ADMIN_USERNAME, "contrasena": "incorrecta"},
            )
            assert response.status_code != 429

        excedido = client.post(
            "/api/v1/auth/login",
            json={"usuario": ADMIN_USERNAME, "contrasena": "incorrecta"},
        )
        assert excedido.status_code == 429
    finally:
        limiter.reset()
        _liberar(engine)
