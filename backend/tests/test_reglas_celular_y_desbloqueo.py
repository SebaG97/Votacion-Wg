"""DEC-039: celular compartido entre matrimonios distintos controlado en vivo
(no solo al importar) y desbloqueo de unidades por resolucion administrativa."""

from __future__ import annotations

import pytest

from app.models import IncidenciaPadron, OpcionVoto
from app.models.enums import (
    EstadoPersona,
    EstadoUnidadElectoral,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
)
from app.services.habilitacion import MOTIVO_CELULAR_DUPLICADO, consultar_habilitacion
from app.services.padron.administracion import actualizar_persona, resolver_incidencia
from app.services.voto import CelularCompartidoError, registrar_voto
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


def _incidencia(db, tipo, persona=None, grupo=None) -> IncidenciaPadron:
    incidencia = IncidenciaPadron(
        tipo=tipo,
        severidad=SeveridadIncidencia.CRITICA,
        persona_id=persona.id if persona else None,
        grupo_id=grupo.id if grupo else None,
    )
    db.add(incidencia)
    db.flush()
    return incidencia


def _dos_matrimonios(db):
    a1 = _persona(db, "Ana", "Uno", "0981111111")
    a2 = _persona(db, "Beto", "Uno", None)
    u1 = _unidad_matrimonio(db, _matrimonio(db, a1, a2))
    b1 = _persona(db, "Caro", "Dos", "0982222222")
    b2 = _persona(db, "Dani", "Dos", None)
    u2 = _unidad_matrimonio(db, _matrimonio(db, b1, b2))
    return a1, u1, b2, u2


def test_celular_editado_igual_al_de_otro_matrimonio_bloquea_la_consulta(db_session):
    db = db_session
    _votacion_abierta(db)
    _a1, _u1, b2, _u2 = _dos_matrimonios(db)
    db.commit()

    actualizar_persona(
        db, persona_id=b2.id, nombres="Dani", apellidos="Dos", documento=None,
        celular="0981111111", usuario="op", confirmar_duplicado_celular=True,
    )
    respuesta = consultar_habilitacion(db, "0981111111")

    assert respuesta.habilitado is False
    assert {u.motivo_no_disponible for u in respuesta.unidades} == {MOTIVO_CELULAR_DUPLICADO}


def test_celular_compartido_entre_matrimonios_no_puede_votar(db_session):
    db = db_session
    votacion = _votacion_abierta(db)
    opcion = _opcion(db, votacion)
    a1, u1, b2, _u2 = _dos_matrimonios(db)
    b2.celular = "0981111111"
    db.commit()

    with pytest.raises(CelularCompartidoError):
        registrar_voto(
            db, votacion_id=votacion.id, celular_consultado="0981111111",
            unidad_electoral_id=u1.id, opcion_id=opcion.id, emitido_por_persona_id=a1.id,
        )


def test_celular_compartido_con_el_conyuge_sigue_permitido(db_session):
    db = db_session
    _votacion_abierta(db)
    a1 = _persona(db, "Ana", "Uno", "0981111111")
    a2 = _persona(db, "Beto", "Uno", "0981111111")
    _unidad_matrimonio(db, _matrimonio(db, a1, a2))
    db.commit()

    assert consultar_habilitacion(db, "0981111111").habilitado is True


def test_cargar_celular_a_matrimonio_sin_celular_lo_habilita(db_session):
    db = db_session
    _votacion_abierta(db)
    e1 = _persona(db, "Eva", "Tres", None)
    e2 = _persona(db, "Fer", "Tres", None)
    unidad = _unidad_matrimonio(
        db, _matrimonio(db, e1, e2), estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
    )
    for p in (e1, e2):
        _incidencia(db, TipoIncidenciaPadron.MATRIMONIO_SIN_CELULAR_DISPONIBLE, persona=p)
    db.commit()

    actualizar_persona(
        db, persona_id=e1.id, nombres="Eva", apellidos="Tres", documento=None,
        celular="0983333333", usuario="op",
    )

    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.HABILITADA.value
    respuesta = consultar_habilitacion(db, "0983333333")
    assert respuesta.habilitado is True
    pendientes = db.query(IncidenciaPadron).filter(IncidenciaPadron.resuelto_at.is_(None)).count()
    assert pendientes == 0


def test_resolver_la_ultima_incidencia_critica_habilita_la_unidad(db_session):
    db = db_session
    _votacion_abierta(db)
    g1 = _persona(db, "Gil", "Cuatro", "0984444444")
    g2 = _persona(db, "Hebe", "Cuatro", None)
    unidad = _unidad_matrimonio(
        db, _matrimonio(db, g1, g2), estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
    )
    primera = _incidencia(db, TipoIncidenciaPadron.CI_DUPLICADA, persona=g1)
    segunda = _incidencia(db, TipoIncidenciaPadron.CONSAGRACION_INCONSISTENTE, persona=g2)
    db.commit()

    resolver_incidencia(db, incidencia_id=primera.id, usuario="op")
    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value

    resolver_incidencia(db, incidencia_id=segunda.id, usuario="op")
    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.HABILITADA.value


def test_resolver_incidencia_de_circulo_habilita_el_bloque(db_session):
    db = db_session
    _votacion_abierta(db)
    grupo = _grupo(db, "Circulo 1")
    unidad = _unidad_bloque(db, grupo, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA)
    incidencia = _incidencia(db, TipoIncidenciaPadron.CIRCULO_SIN_JEFE, grupo=grupo)
    db.commit()

    resolver_incidencia(db, incidencia_id=incidencia.id, usuario="op")

    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.HABILITADA.value


@pytest.mark.parametrize(
    "estado",
    [
        EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA,
        EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES,
    ],
)
def test_resolver_nunca_habilita_bajas_ni_postulantes(db_session, estado):
    db = db_session
    _votacion_abierta(db)
    grupo = _grupo(db, "Circulo Postulantes")
    unidad = _unidad_bloque(db, grupo, estado=estado)
    incidencia = _incidencia(db, TipoIncidenciaPadron.CIRCULO_SIN_JEFE, grupo=grupo)
    db.commit()

    resolver_incidencia(db, incidencia_id=incidencia.id, usuario="op")

    db.refresh(unidad)
    assert unidad.estado == estado.value


def test_resolver_bloque_de_postulantes_lo_deja_pendiente_y_no_habilitado(db_session):
    db = db_session
    _votacion_abierta(db)
    grupo = _grupo(db, "POSTULANTES 2026 A")
    unidad = _unidad_bloque(db, grupo, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA)
    primera = _incidencia(db, TipoIncidenciaPadron.CIRCULO_SIN_JEFE, grupo=grupo)
    segunda = _incidencia(db, TipoIncidenciaPadron.JEFE_SIN_PERSONA_EN_PADRON, grupo=grupo)
    db.commit()

    resolver_incidencia(db, incidencia_id=primera.id, usuario="op")
    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value

    resolver_incidencia(db, incidencia_id=segunda.id, usuario="op")
    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES.value


def test_resolver_matrimonio_sin_activos_lo_deja_pendiente_de_baja(db_session):
    db = db_session
    _votacion_abierta(db)
    b1 = _persona(db, "Ivo", "Cinco", "0985555555", estado=EstadoPersona.BAJA_NO_ML)
    b2 = _persona(db, "Juli", "Cinco", None, estado=EstadoPersona.BAJA_OBSERVACION)
    unidad = _unidad_matrimonio(
        db, _matrimonio(db, b1, b2), estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
    )
    incidencia = _incidencia(db, TipoIncidenciaPadron.CONSAGRACION_INCONSISTENTE, persona=b1)
    db.commit()

    resolver_incidencia(db, incidencia_id=incidencia.id, usuario="op")

    db.refresh(unidad)
    assert unidad.estado == EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA.value


# DEC-040: solo las personas ACTIVA votan.


def test_persona_de_baja_no_habilita_nada_con_su_celular(db_session):
    from app.models.enums import EstadoPersona

    db = db_session
    _votacion_abierta(db)
    baja = _persona(db, "Gil", "Cinco", "0984444444", estado=EstadoPersona.BAJA_NO_ML)
    activa = _persona(db, "Hebe", "Cinco", "0985555555")
    _unidad_matrimonio(db, _matrimonio(db, baja, activa))
    db.commit()

    assert consultar_habilitacion(db, "0984444444").habilitado is False
    assert consultar_habilitacion(db, "0985555555").habilitado is True


def test_celular_compartido_con_conyuge_de_baja_solo_ofrece_al_activo(db_session):
    from app.models.enums import EstadoPersona

    db = db_session
    _votacion_abierta(db)
    baja = _persona(db, "Ines", "Seis", "0986666666", estado=EstadoPersona.BAJA_OBSERVACION)
    activa = _persona(db, "Juan", "Seis", "0986666666")
    _unidad_matrimonio(db, _matrimonio(db, baja, activa))
    db.commit()

    respuesta = consultar_habilitacion(db, "0986666666")
    assert respuesta.habilitado is True
    assert [p.persona_id for p in respuesta.personas] == [activa.id]


def test_persona_de_baja_no_puede_emitir_el_voto_del_matrimonio(db_session):
    from app.models.enums import EstadoPersona
    from app.services.voto import PersonaNoAutorizadaError

    db = db_session
    votacion = _votacion_abierta(db)
    opcion = _opcion(db, votacion)
    baja = _persona(db, "Kari", "Siete", "0987777777", estado=EstadoPersona.BAJA_NO_ML)
    activa = _persona(db, "Leo", "Siete", "0987777777")
    unidad = _unidad_matrimonio(db, _matrimonio(db, baja, activa))
    db.commit()

    with pytest.raises(PersonaNoAutorizadaError):
        registrar_voto(
            db, votacion_id=votacion.id, celular_consultado="0987777777",
            unidad_electoral_id=unidad.id, opcion_id=opcion.id, emitido_por_persona_id=baja.id,
        )
    voto = registrar_voto(
        db, votacion_id=votacion.id, celular_consultado="0987777777",
        unidad_electoral_id=unidad.id, opcion_id=opcion.id, emitido_por_persona_id=activa.id,
    )
    assert voto.emitido_por_persona_id == activa.id


def test_jefe_de_baja_no_vota_por_el_bloque(db_session):
    from app.models.enums import EstadoPersona

    db = db_session
    _votacion_abierta(db)
    grupo = _grupo(db, "Circulo 9")
    _persona(
        db, "Mario", "Ocho", "0988888888",
        estado=EstadoPersona.BAJA_NO_ML, es_jefe_grupo=True, grupo_id=grupo.id,
    )
    _unidad_bloque(db, grupo)
    db.commit()

    assert consultar_habilitacion(db, "0988888888").habilitado is False
