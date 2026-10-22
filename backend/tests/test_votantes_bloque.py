"""DEC-042: el bloque de un grupo de postulantes lo vota su jefe y, si no
tiene jefe activo, su educador; el de un grupo mixto, el jefe aunque haya
quedado en la parte consagrada."""

from __future__ import annotations

import pytest

from app.models import IncidenciaPadron, OpcionVoto
from app.models.enums import (
    EstadoPersona,
    EstadoUnidadElectoral,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
)
from app.services.habilitacion import consultar_habilitacion
from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque
from app.services.voto import CelularNoResuelveUnidadError, registrar_voto
from tests.test_habilitacion import (
    _grupo,
    _matrimonio,
    _persona,
    _unidad_bloque,
    _unidad_matrimonio,
    _votacion_abierta,
)


def _opcion(db, votacion) -> OpcionVoto:
    opcion = OpcionVoto(votacion_id=votacion.id, nombre="Lista A")
    db.add(opcion)
    db.flush()
    return opcion


def _postulantes(db, nombre: str, *, con_jefe: bool):
    """Circulo de postulantes con un matrimonio no consagrado (jefe o no)."""
    grupo = _grupo(db, nombre)
    p1 = _persona(db, "Pablo", "Postulante", "0991000001", grupo_id=grupo.id, es_jefe_grupo=con_jefe)
    p2 = _persona(db, "Paula", "Postulante", None, grupo_id=grupo.id, es_jefe_grupo=con_jefe)
    _matrimonio(db, p1, p2, grupo_id=grupo.id).es_consagrado = False
    bloque = _unidad_bloque(
        db, grupo, estado=EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES
    )
    return grupo, p1, bloque


def _educador_gauto_borja(db, **estado):
    """El educador de POSTULANTES 2022 "B" segun `EDUCADORES`: consagrado de otro circulo."""
    otro = _grupo(db, "CIRCULO 37")
    e1 = _persona(db, "Gilberto", "GAUTO", "0981000002", grupo_id=otro.id, **estado)
    e2 = _persona(db, "Fulvia Beatriz", "BORJA", "0981000003", grupo_id=otro.id, **estado)
    matrimonio = _matrimonio(db, e1, e2, grupo_id=otro.id)
    _unidad_matrimonio(db, matrimonio)
    return e1, matrimonio


def test_sin_jefe_el_educador_vota_el_bloque_ademas_de_su_matrimonio(db_session):
    db = db_session
    votacion = _votacion_abierta(db)
    _grupo_p, postulante, bloque = _postulantes(db, 'POSTULANTES 2022 "B"', con_jefe=False)
    educador, matrimonio = _educador_gauto_borja(db)
    db.commit()

    aplicar_votantes_de_bloque(db)
    db.commit()

    assert bloque.votante_matrimonio_id == matrimonio.id
    assert bloque.estado == EstadoUnidadElectoral.HABILITADA.value
    unidades = {u.unidad_electoral_id for u in consultar_habilitacion(db, "0981000002").unidades}
    assert bloque.id in unidades and len(unidades) == 2
    # El postulante no lo ve: lo vota el educador.
    assert consultar_habilitacion(db, "0991000001").unidades == []

    opcion = _opcion(db, votacion)
    with pytest.raises(CelularNoResuelveUnidadError):
        registrar_voto(
            db, votacion_id=votacion.id, celular_consultado="0991000001",
            unidad_electoral_id=bloque.id, opcion_id=opcion.id, emitido_por_persona_id=postulante.id,
        )
    voto = registrar_voto(
        db, votacion_id=votacion.id, celular_consultado="0981000002",
        unidad_electoral_id=bloque.id, opcion_id=opcion.id, emitido_por_persona_id=educador.id,
    )
    assert voto.unidad_electoral_id == bloque.id


@pytest.mark.parametrize("estado_educador", [EstadoPersona.ACTIVA, EstadoPersona.BAJA_NO_ML])
def test_con_jefe_vota_el_jefe_aunque_haya_educador(db_session, estado_educador):
    db = db_session
    _votacion_abierta(db)
    _g, _jefe, bloque = _postulantes(db, 'POSTULANTES 2022 "B"', con_jefe=True)
    _educador_gauto_borja(db, estado=estado_educador)
    db.commit()

    aplicar_votantes_de_bloque(db)
    db.commit()

    assert bloque.votante_matrimonio_id is None
    assert bloque.estado == EstadoUnidadElectoral.HABILITADA.value
    assert [u.unidad_electoral_id for u in consultar_habilitacion(db, "0991000001").unidades] == [bloque.id]


def test_postulantes_sin_educador_ni_jefe_no_votan(db_session):
    db = db_session
    _postulantes(db, "POSTULANTES 2030 Z", con_jefe=False)
    db.commit()

    aplicar_votantes_de_bloque(db)
    db.commit()

    bloque = _bloque(db)
    assert bloque.estado == EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES.value


def _bloque(db):
    from app.models import UnidadElectoral
    from app.models.enums import TipoUnidadElectoral

    return db.query(UnidadElectoral).filter(
        UnidadElectoral.tipo == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO
    ).one()


def test_grupo_mixto_lo_vota_el_jefe_de_la_parte_consagrada(db_session):
    db = db_session
    _votacion_abierta(db)
    grupo, _p, bloque = _postulantes(db, 'POSTULANTES 2021 "C"', con_jefe=False)
    db.add(
        IncidenciaPadron(
            tipo=TipoIncidenciaPadron.CIRCULO_SIN_JEFE,
            severidad=SeveridadIncidencia.CRITICA,
            grupo_id=grupo.id,
        )
    )
    bloque.estado = EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value
    consagrados = _grupo(db, 'POSTULANTES 2021 "C"/64')
    j1 = _persona(db, "Hector", "MORAN", "0981000004", grupo_id=consagrados.id, es_jefe_grupo=True)
    j2 = _persona(db, "Olga", "GONZALEZ", None, grupo_id=consagrados.id, es_jefe_grupo=True)
    _unidad_matrimonio(db, _matrimonio(db, j1, j2, grupo_id=consagrados.id))
    db.commit()

    aplicar_votantes_de_bloque(db)
    db.commit()

    assert bloque.votante_matrimonio_id == j1.matrimonio_id
    assert bloque.estado == EstadoUnidadElectoral.HABILITADA.value
    assert db.query(IncidenciaPadron).one().resuelto_por == "DEC-042"
    unidades = {u.unidad_electoral_id for u in consultar_habilitacion(db, "0981000004").unidades}
    assert bloque.id in unidades
