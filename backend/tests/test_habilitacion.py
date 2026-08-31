"""Pruebas del motor de habilitacion por celular (Mision 05).

Los datos se arman directo con los modelos SQLAlchemy sobre un SQLite
migrado por prueba (`db_session`, `conftest.py`), no con el Excel real.
"""

from __future__ import annotations

import pytest

from app.models import (
    Grupo,
    IncidenciaPadron,
    Matrimonio,
    OpcionVoto,
    Persona,
    UnidadElectoral,
    Votacion,
    Voto,
)
from app.models.enums import (
    EstadoUnidadElectoral,
    EstadoVotacion,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)
from app.services.habilitacion import NoHayVotacionAbiertaError, consultar_habilitacion


def _votacion_abierta(db) -> Votacion:
    votacion = Votacion(nombre="Votacion De Prueba", estado=EstadoVotacion.ABIERTA)
    db.add(votacion)
    db.flush()
    return votacion


def _grupo(db, nombre: str) -> Grupo:
    grupo = Grupo(nombre=nombre, nombre_normalizado=nombre.upper())
    db.add(grupo)
    db.flush()
    return grupo


def _persona(db, nombres: str, apellidos: str, celular: str | None, **kwargs) -> Persona:
    persona = Persona(nombres=nombres, apellidos=apellidos, celular=celular, **kwargs)
    db.add(persona)
    db.flush()
    return persona


def _matrimonio(db, integrante_1: Persona, integrante_2: Persona | None = None, **kwargs) -> Matrimonio:
    matrimonio = Matrimonio(
        integrante_1_id=integrante_1.id,
        integrante_2_id=integrante_2.id if integrante_2 else None,
        es_consagrado=True,
        **kwargs,
    )
    db.add(matrimonio)
    db.flush()
    integrante_1.matrimonio_id = matrimonio.id
    if integrante_2:
        integrante_2.matrimonio_id = matrimonio.id
    db.flush()
    return matrimonio


def _unidad_matrimonio(db, matrimonio: Matrimonio, estado=EstadoUnidadElectoral.HABILITADA) -> UnidadElectoral:
    unidad = UnidadElectoral(
        tipo=TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
        referencia_id=matrimonio.id,
        grupo_id=matrimonio.grupo_id,
        estado=estado.value,
    )
    db.add(unidad)
    db.flush()
    return unidad


def _unidad_bloque(db, grupo: Grupo, estado=EstadoUnidadElectoral.HABILITADA) -> UnidadElectoral:
    unidad = UnidadElectoral(
        tipo=TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
        referencia_id=grupo.id,
        grupo_id=grupo.id,
        estado=estado.value,
    )
    db.add(unidad)
    db.flush()
    return unidad


def _votar(db, votacion: Votacion, unidad: UnidadElectoral) -> Voto:
    opcion = OpcionVoto(votacion_id=votacion.id, nombre="Opcion Unica")
    db.add(opcion)
    db.flush()
    voto = Voto(votacion_id=votacion.id, unidad_electoral_id=unidad.id, opcion_id=opcion.id)
    db.add(voto)
    db.flush()
    return voto


def test_celular_inexistente_no_habilitado(db_session):
    _votacion_abierta(db_session)

    respuesta = consultar_habilitacion(db_session, "0987654321")

    assert respuesta.habilitado is False
    assert respuesta.personas == []
    assert respuesta.unidades == []


def test_celular_con_formato_invalido_no_habilitado(db_session):
    _votacion_abierta(db_session)

    respuesta = consultar_habilitacion(db_session, "abc")

    assert respuesta.habilitado is False
    assert respuesta.celular_normalizado is None
    assert respuesta.unidades == []


def test_unidad_bloqueada_por_incidencia_responde_la_incidencia_y_no_ofrece_voto(db_session):
    votacion = _votacion_abierta(db_session)
    grupo = _grupo(db_session, "CIRCULO 1")
    persona = _persona(db_session, "Ana", "Gomez", "0981000001", grupo_id=grupo.id)
    matrimonio = _matrimonio(db_session, persona, grupo_id=grupo.id)
    _unidad_matrimonio(db_session, matrimonio, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA)
    db_session.add(
        IncidenciaPadron(
            tipo=TipoIncidenciaPadron.CELULAR_DUPLICADO,
            severidad=SeveridadIncidencia.CRITICA,
            descripcion="Celular duplicado entre matrimonios distintos.",
            persona_id=persona.id,
        )
    )
    db_session.flush()

    respuesta = consultar_habilitacion(db_session, "0981000001")

    assert respuesta.habilitado is False
    assert len(respuesta.unidades) == 1
    unidad = respuesta.unidades[0]
    assert unidad.disponible is False
    assert unidad.motivo_no_disponible == "BLOQUEADA_POR_INCIDENCIA"
    assert len(unidad.incidencias) == 1
    assert unidad.incidencias[0].tipo == TipoIncidenciaPadron.CELULAR_DUPLICADO


def test_unidad_con_voto_registrado_no_se_vuelve_a_ofrecer(db_session):
    votacion = _votacion_abierta(db_session)
    persona = _persona(db_session, "Ana", "Gomez", "0981000001")
    matrimonio = _matrimonio(db_session, persona)
    unidad = _unidad_matrimonio(db_session, matrimonio)
    _votar(db_session, votacion, unidad)

    respuesta = consultar_habilitacion(db_session, "0981000001")

    assert respuesta.habilitado is False
    assert len(respuesta.unidades) == 1
    assert respuesta.unidades[0].disponible is False
    assert respuesta.unidades[0].motivo_no_disponible == "YA_VOTADO"


def test_jefe_consagrado_con_doble_rol_ve_dos_unidades_evaluadas_por_separado(db_session):
    votacion = _votacion_abierta(db_session)
    grupo = _grupo(db_session, "CIRCULO 2")
    persona = _persona(
        db_session, "Juan", "Perez", "0981000002", grupo_id=grupo.id, es_jefe_grupo=True
    )
    matrimonio = _matrimonio(db_session, persona, grupo_id=grupo.id)
    unidad_matrimonio = _unidad_matrimonio(db_session, matrimonio)
    unidad_bloque = _unidad_bloque(db_session, grupo)
    _votar(db_session, votacion, unidad_bloque)

    respuesta = consultar_habilitacion(db_session, "0981000002")

    assert len(respuesta.unidades) == 2
    por_tipo = {u.tipo: u for u in respuesta.unidades}
    assert por_tipo[TipoUnidadElectoral.MATRIMONIO_CONSAGRADO].disponible is True
    assert por_tipo[TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO].disponible is False
    assert por_tipo[TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO].motivo_no_disponible == "YA_VOTADO"
    assert respuesta.habilitado is True


def test_celular_compartido_entre_conyuges_resuelve_a_una_sola_unidad(db_session):
    _votacion_abierta(db_session)
    esposo = _persona(db_session, "Juan", "Perez", "0981000003")
    esposa = _persona(db_session, "Maria", "Lopez", "0981000003")
    matrimonio = _matrimonio(db_session, esposo, esposa)
    _unidad_matrimonio(db_session, matrimonio)

    respuesta = consultar_habilitacion(db_session, "0981000003")

    assert len(respuesta.personas) == 2
    assert len(respuesta.unidades) == 1
    assert respuesta.unidades[0].disponible is True
    assert respuesta.habilitado is True


def test_sin_votacion_abierta_levanta_error_explicito(db_session):
    with pytest.raises(NoHayVotacionAbiertaError):
        consultar_habilitacion(db_session, "0981000001")
