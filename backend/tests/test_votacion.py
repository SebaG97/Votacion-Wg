"""Pruebas de administracion de votacion (Mision 07): crear, cargar opciones,
abrir, cerrar y consultar el estado operativo.

Los datos se arman directo con los modelos SQLAlchemy sobre un SQLite
migrado por prueba (`db_session`, `conftest.py`), reusando los helpers de
armado de `test_habilitacion.py` (Mision 05).
"""

from __future__ import annotations

import pytest

from app.models import OpcionVoto, UnidadElectoral, Votacion, Voto
from app.models.enums import EstadoUnidadElectoral, EstadoVotacion
from app.services import votacion as votacion_service
from app.services.votacion import (
    OtraVotacionAbiertaError,
    VotacionNoAbiertaError,
    VotacionNoEncontradaError,
    VotacionNoEsBorradorError,
    VotacionSinOpcionesError,
    abrir_votacion,
    agregar_opcion,
    cerrar_votacion,
    crear_votacion,
    listar_opciones,
    obtener_estado_operativo,
)
from tests.test_habilitacion import _grupo, _matrimonio, _persona, _unidad_bloque, _unidad_matrimonio


def test_crear_votacion_queda_en_borrador(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")

    assert votacion.id is not None
    assert votacion.estado == EstadoVotacion.BORRADOR
    assert votacion.abierta_por is None
    assert votacion.cerrada_por is None


def test_agregar_opcion_funciona_en_borrador(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")

    opcion = agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A", orden=1)

    assert opcion.id is not None
    assert opcion.votacion_id == votacion.id
    assert listar_opciones(db_session, votacion.id) == [opcion]


def test_agregar_opcion_404_si_la_votacion_no_existe(db_session):
    with pytest.raises(VotacionNoEncontradaError):
        agregar_opcion(db_session, votacion_id=9999, nombre="Lista A")


@pytest.mark.parametrize("estado", [EstadoVotacion.ABIERTA, EstadoVotacion.CERRADA])
def test_agregar_opcion_409_si_la_votacion_ya_no_esta_en_borrador(db_session, estado):
    votacion = Votacion(nombre="Consejo 2026", estado=estado)
    db_session.add(votacion)
    db_session.commit()

    with pytest.raises(VotacionNoEsBorradorError):
        agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista Tardia")


def test_abrir_sin_opciones_da_409(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")

    with pytest.raises(VotacionSinOpcionesError):
        abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")


def test_abrir_con_opciones_y_sin_otra_abierta_ok(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")

    abierta = abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    assert abierta.estado == EstadoVotacion.ABIERTA
    assert abierta.abierta_por == "admin@wg"
    assert abierta.fecha_apertura is not None


def test_abrir_da_409_si_ya_esta_fuera_de_borrador(db_session):
    votacion = Votacion(nombre="Consejo 2026", estado=EstadoVotacion.CERRADA)
    db_session.add(votacion)
    db_session.commit()

    with pytest.raises(VotacionNoEsBorradorError):
        abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")


def test_abrir_da_409_si_ya_hay_otra_abierta(db_session):
    otra = Votacion(nombre="Ya Abierta", estado=EstadoVotacion.ABIERTA)
    db_session.add(otra)
    db_session.commit()

    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")

    with pytest.raises(OtraVotacionAbiertaError):
        abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")


def test_carrera_de_dos_aperturas_simultaneas_se_resuelve_como_409_no_500(
    db_session, monkeypatch
):
    """Simula dos requests que pasan el chequeo previo a la vez: se bypassea
    `_confirmar_sin_otra_abierta` (no-op) e se abre una segunda votacion
    competidora directo por fuera del chequeo, justo antes de que
    `abrir_votacion` intente su propio commit. El indice unico parcial
    `uq_votacion_estado_abierta` debe traducirse a 409, no a un 500 sin
    manejar -- mismo patron que `test_voto.py::test_carrera_de_dos_inserts_simultaneos...`."""
    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")

    monkeypatch.setattr(votacion_service, "_confirmar_sin_otra_abierta", lambda *a, **k: None)

    competidora = Votacion(nombre="Competidora", estado=EstadoVotacion.ABIERTA)
    db_session.add(competidora)
    db_session.commit()

    with pytest.raises(OtraVotacionAbiertaError):
        abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    db_session.rollback()
    persistida = db_session.get(Votacion, votacion.id)
    assert persistida.estado == EstadoVotacion.BORRADOR

    total_abiertas = (
        db_session.query(Votacion).filter(Votacion.estado == EstadoVotacion.ABIERTA).count()
    )
    assert total_abiertas == 1


def test_cerrar_una_abierta_ok(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")
    abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    cerrada = cerrar_votacion(db_session, votacion_id=votacion.id, usuario="otro-admin@wg")

    assert cerrada.estado == EstadoVotacion.CERRADA
    assert cerrada.cerrada_por == "otro-admin@wg"
    assert cerrada.fecha_cierre is not None


@pytest.mark.parametrize("estado", [EstadoVotacion.BORRADOR, EstadoVotacion.CERRADA])
def test_cerrar_una_no_abierta_da_409(db_session, estado):
    votacion = Votacion(nombre="Consejo 2026", estado=estado)
    db_session.add(votacion)
    db_session.commit()

    with pytest.raises(VotacionNoAbiertaError):
        cerrar_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")


def test_cerrar_404_si_la_votacion_no_existe(db_session):
    with pytest.raises(VotacionNoEncontradaError):
        cerrar_votacion(db_session, votacion_id=9999, usuario="admin@wg")


def test_estado_operativo_refleja_conteos_y_no_expone_nada_por_opcion(db_session):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    opcion_a = agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")
    opcion_b = agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista B")
    abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    grupo = _grupo(db_session, "CIRCULO 1")
    persona_1 = _persona(db_session, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
    persona_2 = _persona(db_session, "Beto", "Diaz", "0981000002", grupo_id=grupo.id)
    persona_3 = _persona(db_session, "Cris", "Paez", "0981000003", grupo_id=grupo.id)
    matrimonio_1 = _matrimonio(db_session, persona_1, grupo_id=grupo.id)
    matrimonio_2 = _matrimonio(db_session, persona_2, grupo_id=grupo.id)
    matrimonio_3 = _matrimonio(db_session, persona_3, grupo_id=grupo.id)

    unidad_votada = _unidad_matrimonio(db_session, matrimonio_1)
    _unidad_matrimonio(db_session, matrimonio_2)  # HABILITADA, sin voto: pendiente
    _unidad_matrimonio(
        db_session, matrimonio_3, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
    )
    _unidad_bloque(db_session, grupo, estado=EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA)

    voto = Voto(votacion_id=votacion.id, unidad_electoral_id=unidad_votada.id, opcion_id=opcion_a.id)
    db_session.add(voto)
    db_session.commit()

    respuesta = obtener_estado_operativo(db_session, votacion.id)

    assert respuesta["votacion_id"] == votacion.id
    assert respuesta["estado"] == EstadoVotacion.ABIERTA
    assert respuesta["unidades_por_estado"]["habilitada"] == 2
    assert respuesta["unidades_por_estado"]["bloqueada_por_incidencia"] == 1
    assert respuesta["unidades_por_estado"]["pendiente_definicion_baja"] == 1
    assert respuesta["unidades_por_estado"]["pendiente_definicion_postulantes"] == 0
    assert respuesta["votos_emitidos"] == 1
    assert respuesta["pendientes"] == 1

    # Nada agrupado por opcion: ni las claves de nivel superior ni las de
    # `unidades_por_estado` referencian `opcion_a`/`opcion_b` de ninguna forma.
    assert set(respuesta.keys()) == {
        "votacion_id",
        "estado",
        "unidades_por_estado",
        "votos_emitidos",
        "pendientes",
    }
    assert "opcion_id" not in respuesta
    assert not any("opcion" in clave for clave in respuesta["unidades_por_estado"])


def test_estado_operativo_404_si_la_votacion_no_existe(db_session):
    with pytest.raises(VotacionNoEncontradaError):
        obtener_estado_operativo(db_session, 9999)
