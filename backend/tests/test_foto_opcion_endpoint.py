"""Pruebas de la foto de cada opcion (Mision 15, DEC-037): subir, reemplazar,
quitar, servirla publicamente, validaciones y control de acceso."""

from __future__ import annotations

from app.core.config import settings
from tests.test_votacion_endpoint import ADMIN_TOKEN, _cliente_con_db, _headers, _liberar

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _votacion_con_opcion(client) -> tuple[int, int]:
    votacion_id = client.post(
        "/api/v1/votaciones", json={"nombre": "Simulacro"}, headers=_headers()
    ).json()["id"]
    opcion_id = client.post(
        f"/api/v1/votaciones/{votacion_id}/opciones",
        json={"nombre": "Matrimonio A"},
        headers=_headers(),
    ).json()["id"]
    return votacion_id, opcion_id


def _subir(client, votacion_id, opcion_id, contenido=PNG, tipo="image/png", headers=None):
    return client.put(
        f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto",
        content=contenido,
        headers={**(_headers() if headers is None else headers), "Content-Type": tipo},
    )


def test_subir_foto_y_servirla_publicamente(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)

        response = _subir(client, votacion_id, opcion_id)
        assert response.status_code == 200
        assert response.json()["tiene_foto"] is True

        opciones = client.get(
            f"/api/v1/votaciones/{votacion_id}/opciones", headers=_headers()
        ).json()
        assert opciones[0]["tiene_foto"] is True

        foto = client.get(f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto")
        assert foto.status_code == 200
        assert foto.headers["content-type"] == "image/png"
        assert foto.content == PNG
    finally:
        _liberar(engine)


def test_reemplazar_y_quitar_foto(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)
        _subir(client, votacion_id, opcion_id)
        _subir(client, votacion_id, opcion_id, contenido=b"jpeg-bytes", tipo="image/jpeg")

        foto = client.get(f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto")
        assert foto.headers["content-type"] == "image/jpeg"
        assert foto.content == b"jpeg-bytes"

        borrar = client.delete(
            f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto", headers=_headers()
        )
        assert borrar.status_code == 200
        assert borrar.json()["tiene_foto"] is False
        assert (
            client.get(f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto").status_code
            == 404
        )
    finally:
        _liberar(engine)


def test_foto_tipo_no_admitido_vacia_o_muy_grande_da_422(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)

        assert _subir(client, votacion_id, opcion_id, tipo="application/pdf").status_code == 422
        assert _subir(client, votacion_id, opcion_id, contenido=b"").status_code == 422
        grande = b"0" * (1024 * 1024 + 1)
        assert _subir(client, votacion_id, opcion_id, contenido=grande).status_code == 422
    finally:
        _liberar(engine)


def test_foto_de_opcion_de_otra_votacion_da_404(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)
        otra_id, _ = _votacion_con_opcion(client)

        assert _subir(client, otra_id, opcion_id).status_code == 404
        assert (
            client.get(f"/api/v1/votaciones/{otra_id}/opciones/{opcion_id}/foto").status_code
            == 404
        )
        # Sin foto cargada tambien es 404, no un 200 vacio.
        assert (
            client.get(f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto").status_code
            == 404
        )
    finally:
        _liberar(engine)


def test_no_se_puede_cambiar_la_foto_con_la_votacion_abierta(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)
        _subir(client, votacion_id, opcion_id)
        client.post(
            f"/api/v1/votaciones/{votacion_id}/abrir",
            json={"usuario": "admin@wg"},
            headers=_headers(),
        )

        assert _subir(client, votacion_id, opcion_id).status_code == 409
        assert (
            client.delete(
                f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto", headers=_headers()
            ).status_code
            == 409
        )

        papeleta = client.get("/api/v1/votaciones/abierta").json()
        assert papeleta["opciones"][0]["tiene_foto"] is True
        # La foto se sigue sirviendo con la votacion abierta.
        assert (
            client.get(f"/api/v1/votaciones/{votacion_id}/opciones/{opcion_id}/foto").status_code
            == 200
        )
    finally:
        _liberar(engine)


def test_subir_foto_sin_token_da_401_o_403(migrated_db_url, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", ADMIN_TOKEN)
    client, engine = _cliente_con_db(migrated_db_url)
    try:
        votacion_id, opcion_id = _votacion_con_opcion(client)
        response = _subir(client, votacion_id, opcion_id, headers={})
        assert response.status_code in (401, 403)
    finally:
        _liberar(engine)
