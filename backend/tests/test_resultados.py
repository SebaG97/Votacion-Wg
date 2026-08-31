"""Pruebas de resultados y revelacion de votacion (Mision 08, DEC-022).

Los datos se arman directo con los modelos SQLAlchemy sobre un SQLite
migrado por prueba (`db_session`, `conftest.py`), reusando los helpers de
armado de `test_habilitacion.py` (Mision 05).
"""

from __future__ import annotations

import pytest

from app.models import Votacion, Voto
from app.models.enums import EstadoVotacion, TipoUnidadElectoral
from app.services.votacion import (
    ResultadosBloqueadosError,
    ResultadosYaReveladosError,
    VotacionNoCerradaError,
    VotacionNoEncontradaError,
    abrir_votacion,
    agregar_opcion,
    cerrar_votacion,
    crear_votacion,
    obtener_resultados,
    revelar_resultados,
)
from tests.test_habilitacion import (
    _grupo,
    _matrimonio,
    _persona,
    _unidad_bloque,
    _unidad_matrimonio,
)


def _votar(db, votacion, unidad, opcion) -> Voto:
    voto = Voto(votacion_id=votacion.id, unidad_electoral_id=unidad.id, opcion_id=opcion.id)
    db.add(voto)
    db.flush()
    return voto


def _votacion_cerrada_con_una_opcion(db):
    votacion = crear_votacion(db, nombre="Consejo 2026")
    opcion = agregar_opcion(db, votacion_id=votacion.id, nombre="Lista A")
    abrir_votacion(db, votacion_id=votacion.id, usuario="admin@wg")
    cerrar_votacion(db, votacion_id=votacion.id, usuario="admin@wg")
    return votacion, opcion


@pytest.mark.parametrize("estado", [EstadoVotacion.BORRADOR, EstadoVotacion.ABIERTA])
def test_resultados_bloqueados_en_borrador_o_abierta(db_session, estado):
    votacion = Votacion(nombre="Consejo 2026", estado=estado)
    db_session.add(votacion)
    db_session.commit()

    with pytest.raises(ResultadosBloqueadosError):
        obtener_resultados(db_session, votacion.id)


def test_resultados_404_si_la_votacion_no_existe(db_session):
    with pytest.raises(VotacionNoEncontradaError):
        obtener_resultados(db_session, 9999)


def test_resultados_con_votacion_cerrada_incluye_los_tres_desgloses(db_session):
    votacion, opcion = _votacion_cerrada_con_una_opcion(db_session)

    grupo = _grupo(db_session, "CIRCULO 1")
    persona = _persona(db_session, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
    matrimonio = _matrimonio(db_session, persona, grupo_id=grupo.id)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    _votar(db_session, votacion, unidad, opcion)
    db_session.commit()

    resultado = obtener_resultados(db_session, votacion.id)

    assert resultado["votacion_id"] == votacion.id
    assert resultado["estado"] == EstadoVotacion.CERRADA
    assert resultado["total_votos"] == 1
    assert resultado["totales_por_opcion"] == [
        {"opcion_id": opcion.id, "nombre": "Lista A", "votos": 1, "porcentaje": 100.0}
    ]

    tipo_matrimonio = next(
        t
        for t in resultado["totales_por_tipo_unidad"]
        if t["tipo"] == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO
    )
    assert tipo_matrimonio["votos_emitidos"] == 1
    assert tipo_matrimonio["unidades_habilitadas"] == 1
    assert tipo_matrimonio["participacion"] == 1.0

    tipo_bloque = next(
        t
        for t in resultado["totales_por_tipo_unidad"]
        if t["tipo"] == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO
    )
    assert tipo_bloque["votos_emitidos"] == 0
    assert tipo_bloque["unidades_habilitadas"] == 0
    assert tipo_bloque["participacion"] is None

    grupo_resultado = next(
        g for g in resultado["totales_por_grupo"] if g["grupo_id"] == grupo.id
    )
    assert grupo_resultado["votos_emitidos"] == 1
    assert grupo_resultado["unidades_habilitadas"] == 1
    assert grupo_resultado["participacion"] == 1.0

    # No se cruza grupo x opcion (DEC-022): ninguna fila de `totales_por_grupo`
    # referencia una opcion.
    assert not any(
        "opcion" in clave for fila in resultado["totales_por_grupo"] for clave in fila
    )


def test_resultados_con_resultados_revelados_mismo_contenido_que_cerrada(db_session):
    votacion, opcion = _votacion_cerrada_con_una_opcion(db_session)
    grupo = _grupo(db_session, "CIRCULO 1")
    persona = _persona(db_session, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
    matrimonio = _matrimonio(db_session, persona, grupo_id=grupo.id)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    _votar(db_session, votacion, unidad, opcion)
    db_session.commit()

    antes = obtener_resultados(db_session, votacion.id)
    revelar_resultados(db_session, votacion_id=votacion.id)
    despues = obtener_resultados(db_session, votacion.id)

    assert despues["total_votos"] == antes["total_votos"]
    assert despues["totales_por_opcion"] == antes["totales_por_opcion"]
    assert despues["totales_por_tipo_unidad"] == antes["totales_por_tipo_unidad"]
    assert despues["totales_por_grupo"] == antes["totales_por_grupo"]
    assert despues["estado"] == EstadoVotacion.RESULTADOS_REVELADOS
    assert antes["estado"] == EstadoVotacion.CERRADA


def test_revelar_desde_cerrada_ok_setea_resultados_revelados_at(db_session):
    votacion, _opcion = _votacion_cerrada_con_una_opcion(db_session)

    revelada = revelar_resultados(db_session, votacion_id=votacion.id)

    assert revelada.estado == EstadoVotacion.RESULTADOS_REVELADOS
    assert revelada.resultados_revelados_at is not None


@pytest.mark.parametrize("estado", [EstadoVotacion.BORRADOR, EstadoVotacion.ABIERTA])
def test_revelar_desde_borrador_o_abierta_da_409(db_session, estado):
    votacion = Votacion(nombre="Consejo 2026", estado=estado)
    db_session.add(votacion)
    db_session.commit()

    with pytest.raises(VotacionNoCerradaError):
        revelar_resultados(db_session, votacion_id=votacion.id)


def test_revelar_dos_veces_da_409_explicito(db_session):
    votacion, _opcion = _votacion_cerrada_con_una_opcion(db_session)
    revelar_resultados(db_session, votacion_id=votacion.id)

    with pytest.raises(ResultadosYaReveladosError):
        revelar_resultados(db_session, votacion_id=votacion.id)


def test_revelar_404_si_la_votacion_no_existe(db_session):
    with pytest.raises(VotacionNoEncontradaError):
        revelar_resultados(db_session, votacion_id=9999)


def test_resultados_varias_opciones_y_tipos_de_unidad_los_tres_desgloses_suman_el_total(
    db_session,
):
    votacion = crear_votacion(db_session, nombre="Consejo 2026")
    opcion_a = agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista A")
    opcion_b = agregar_opcion(db_session, votacion_id=votacion.id, nombre="Lista B")
    abrir_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    grupo_1 = _grupo(db_session, "CIRCULO 1")
    grupo_2 = _grupo(db_session, "CIRCULO 2")

    persona_1 = _persona(db_session, "Ana", "Gomez", "0981000001", grupo_id=grupo_1.id)
    persona_3 = _persona(db_session, "Cris", "Paez", "0981000003", grupo_id=grupo_2.id)
    persona_4 = _persona(db_session, "Dora", "Ruiz", "0981000004", grupo_id=grupo_2.id)

    matrimonio_1 = _matrimonio(db_session, persona_1, grupo_id=grupo_1.id)
    matrimonio_3 = _matrimonio(db_session, persona_3, grupo_id=grupo_2.id)
    matrimonio_4 = _matrimonio(db_session, persona_4, grupo_id=grupo_2.id)

    unidad_matrimonio_1 = _unidad_matrimonio(db_session, matrimonio_1)  # votada, opcion A
    unidad_bloque_1 = _unidad_bloque(db_session, grupo_1)  # votada, opcion B
    unidad_matrimonio_3 = _unidad_matrimonio(db_session, matrimonio_3)  # votada, opcion A
    _unidad_matrimonio(db_session, matrimonio_4)  # HABILITADA, sin votar

    _votar(db_session, votacion, unidad_matrimonio_1, opcion_a)
    _votar(db_session, votacion, unidad_bloque_1, opcion_b)
    _votar(db_session, votacion, unidad_matrimonio_3, opcion_a)
    db_session.commit()

    cerrar_votacion(db_session, votacion_id=votacion.id, usuario="admin@wg")

    resultado = obtener_resultados(db_session, votacion.id)

    assert resultado["total_votos"] == 3
    assert sum(f["votos"] for f in resultado["totales_por_opcion"]) == 3
    assert sum(f["votos_emitidos"] for f in resultado["totales_por_tipo_unidad"]) == 3
    assert sum(f["votos_emitidos"] for f in resultado["totales_por_grupo"]) == 3

    por_opcion = {f["opcion_id"]: f["votos"] for f in resultado["totales_por_opcion"]}
    assert por_opcion[opcion_a.id] == 2
    assert por_opcion[opcion_b.id] == 1

    por_tipo = {f["tipo"]: f for f in resultado["totales_por_tipo_unidad"]}
    assert por_tipo[TipoUnidadElectoral.MATRIMONIO_CONSAGRADO]["votos_emitidos"] == 2
    assert por_tipo[TipoUnidadElectoral.MATRIMONIO_CONSAGRADO]["unidades_habilitadas"] == 3
    assert por_tipo[TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO]["votos_emitidos"] == 1
    assert por_tipo[TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO]["unidades_habilitadas"] == 1

    por_grupo = {f["grupo_id"]: f for f in resultado["totales_por_grupo"]}
    assert por_grupo[grupo_1.id]["votos_emitidos"] == 2
    assert por_grupo[grupo_2.id]["votos_emitidos"] == 1
