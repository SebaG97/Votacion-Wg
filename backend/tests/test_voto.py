"""Pruebas del registro de voto (Mision 06).

Los datos se arman directo con los modelos SQLAlchemy sobre un SQLite
migrado por prueba (`db_session`, `conftest.py`), igual que en la Mision 05
(`test_habilitacion.py`), cuyos helpers de armado se reusan.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Matrimonio, OpcionVoto, Persona, UnidadElectoral, Votacion, Voto
from app.models.enums import EstadoUnidadElectoral, EstadoVotacion, TipoUnidadElectoral
from app.services import voto as voto_service
from app.services.voto import (
    CelularNoResuelveUnidadError,
    OpcionInvalidaError,
    PersonaNoAutorizadaError,
    UnidadElectoralNoDisponibleError,
    UnidadElectoralNoEncontradaError,
    VotacionNoDisponibleError,
    VotoDuplicadoError,
    registrar_voto,
)
from tests.test_habilitacion import (
    _grupo,
    _matrimonio,
    _persona,
    _unidad_bloque,
    _unidad_matrimonio,
    _votacion_abierta,
)


def _opcion(db, votacion: Votacion, nombre: str = "Opcion Unica") -> OpcionVoto:
    opcion = OpcionVoto(votacion_id=votacion.id, nombre=nombre)
    db.add(opcion)
    db.flush()
    return opcion


def test_voto_exitoso_se_persiste_con_datos_de_auditoria(db_session):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    voto = registrar_voto(
        db_session,
        votacion_id=votacion.id,
        celular_consultado="0981000001",
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
        canal="whatsapp",
    )

    assert voto.id is not None
    assert voto.votacion_id == votacion.id
    assert voto.unidad_electoral_id == unidad.id
    assert voto.opcion_id == opcion.id
    assert voto.emitido_por_persona_id == persona.id
    assert voto.celular_consultado == "0981000001"
    assert voto.canal == "whatsapp"
    assert voto.fecha_emision is not None

    persistido = db_session.get(Voto, voto.id)
    assert persistido is not None


def test_segundo_intento_sobre_misma_unidad_da_409_y_no_crea_segunda_fila(db_session):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    registrar_voto(
        db_session,
        votacion_id=votacion.id,
        celular_consultado="0981000001",
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
    )

    with pytest.raises(VotoDuplicadoError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=persona.id,
        )

    total = (
        db_session.query(Voto)
        .filter(Voto.votacion_id == votacion.id, Voto.unidad_electoral_id == unidad.id)
        .count()
    )
    assert total == 1


def test_carrera_de_dos_inserts_simultaneos_se_resuelve_como_409_no_500(db_session, monkeypatch):
    """Simula dos requests que pasan el chequeo previo a la vez: se bypassea
    `_confirmar_sin_voto_previo` (no-op) e se inserta un `Voto` competidor
    directo por fuera del chequeo, justo antes de que `registrar_voto` intente
    su propio commit. La restriccion unica de base debe traducirse a 409, no
    a un 500 sin manejar."""
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    monkeypatch.setattr(voto_service, "_confirmar_sin_voto_previo", lambda *a, **k: None)

    voto_competidor = Voto(
        votacion_id=votacion.id,
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
    )
    db_session.add(voto_competidor)
    db_session.commit()

    with pytest.raises(VotoDuplicadoError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=persona.id,
        )

    total = (
        db_session.query(Voto)
        .filter(Voto.votacion_id == votacion.id, Voto.unidad_electoral_id == unidad.id)
        .count()
    )
    assert total == 1


@pytest.mark.parametrize("estado", [EstadoVotacion.BORRADOR, EstadoVotacion.CERRADA])
def test_votacion_no_abierta_da_409(db_session, estado):
    votacion = Votacion(nombre="Votacion De Prueba", estado=estado)
    db_session.add(votacion)
    db_session.flush()
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = OpcionVoto(votacion_id=votacion.id, nombre="Opcion Unica")
    db_session.add(opcion)
    db_session.commit()

    with pytest.raises(VotacionNoDisponibleError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=persona.id,
        )


def test_votacion_inexistente_da_409(db_session):
    with pytest.raises(VotacionNoDisponibleError):
        registrar_voto(
            db_session,
            votacion_id=9999,
            celular_consultado="0981000001",
            unidad_electoral_id=1,
            opcion_id=1,
            emitido_por_persona_id=1,
        )


@pytest.mark.parametrize(
    "estado",
    [
        EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA,
        EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES,
        EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA,
    ],
)
def test_unidad_no_habilitada_da_409_citando_estado_real(db_session, estado):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio, estado=estado)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    with pytest.raises(UnidadElectoralNoDisponibleError) as excinfo:
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=persona.id,
        )
    assert excinfo.value.estado_real == estado.value


def test_unidad_inexistente_da_404(db_session):
    votacion = _votacion_abierta(db_session)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    with pytest.raises(UnidadElectoralNoEncontradaError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=9999,
            opcion_id=opcion.id,
            emitido_por_persona_id=1,
        )


def test_opcion_de_otra_votacion_da_400(db_session):
    votacion = _votacion_abierta(db_session)
    otra_votacion = Votacion(nombre="Otra Votacion", estado=EstadoVotacion.ABIERTA)
    db_session.add(otra_votacion)
    db_session.flush()
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion_de_otra_votacion = _opcion(db_session, otra_votacion)
    db_session.commit()

    with pytest.raises(OpcionInvalidaError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion_de_otra_votacion.id,
            emitido_por_persona_id=persona.id,
        )


def test_celular_que_no_resuelve_a_la_unidad_da_400(db_session):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    with pytest.raises(CelularNoResuelveUnidadError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0987654321",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=persona.id,
        )


def test_persona_no_autorizada_da_400(db_session):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    opcion = _opcion(db_session, votacion)
    ajena = _persona(db_session, "Otra", "Persona", "0981000099")
    db_session.commit()

    with pytest.raises(PersonaNoAutorizadaError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000001",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=ajena.id,
        )


def test_bloque_no_consagrado_exige_jefe_de_ese_grupo(db_session):
    votacion = _votacion_abierta(db_session)
    grupo = _grupo(db_session, "CIRCULO 5")
    jefe = _persona(
        db_session, "Juan", "Perez", "0981000005", grupo_id=grupo.id, es_jefe_grupo=True
    )
    no_jefe = _persona(db_session, "Pedro", "Diaz", "0981000006", grupo_id=grupo.id)
    unidad = _unidad_bloque(db_session, grupo)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    with pytest.raises(PersonaNoAutorizadaError):
        registrar_voto(
            db_session,
            votacion_id=votacion.id,
            celular_consultado="0981000005",
            unidad_electoral_id=unidad.id,
            opcion_id=opcion.id,
            emitido_por_persona_id=no_jefe.id,
        )

    voto = registrar_voto(
        db_session,
        votacion_id=votacion.id,
        celular_consultado="0981000005",
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=jefe.id,
    )
    assert voto.emitido_por_persona_id == jefe.id


def test_jefe_consagrado_con_doble_rol_permite_dos_votos_independientes(db_session):
    """DEC-014 sigue sin resolucion del negocio: esta mision no impone ninguna
    restriccion de "elegi una". Cada unidad se vota de forma independiente."""
    votacion = _votacion_abierta(db_session)
    grupo = _grupo(db_session, "CIRCULO 6")
    persona = _persona(
        db_session, "Juan", "Perez", "0981000007", grupo_id=grupo.id, es_jefe_grupo=True
    )
    matrimonio = _matrimonio(db_session, persona, grupo_id=grupo.id)
    unidad_matrimonio = _unidad_matrimonio(db_session, matrimonio)
    unidad_bloque = _unidad_bloque(db_session, grupo)
    opcion = _opcion(db_session, votacion)
    db_session.commit()

    voto_matrimonio = registrar_voto(
        db_session,
        votacion_id=votacion.id,
        celular_consultado="0981000007",
        unidad_electoral_id=unidad_matrimonio.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
    )
    voto_bloque = registrar_voto(
        db_session,
        votacion_id=votacion.id,
        celular_consultado="0981000007",
        unidad_electoral_id=unidad_bloque.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
    )

    assert voto_matrimonio.id != voto_bloque.id
    assert voto_matrimonio.unidad_electoral_id == unidad_matrimonio.id
    assert voto_bloque.unidad_electoral_id == unidad_bloque.id
