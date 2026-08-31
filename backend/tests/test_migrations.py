import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.models import (
    Grupo,
    ImportacionPadron,
    IncidenciaPadron,
    Matrimonio,
    OpcionVoto,
    Persona,
    UnidadElectoral,
    Votacion,
    Voto,
)
from app.models.enums import EstadoVotacion, SeveridadIncidencia, TipoIncidenciaPadron, TipoUnidadElectoral

EXPECTED_TABLES = {
    "personas",
    "matrimonios",
    "grupos",
    "unidades_electorales",
    "votaciones",
    "opciones_voto",
    "votos",
    "incidencias_padron",
    "importaciones_padron",
    "alembic_version",
}


def test_upgrade_head_crea_todas_las_tablas(migrated_db_url):
    from app.db.session import _build_engine

    engine = _build_engine(migrated_db_url)
    try:
        inspector = inspect(engine)
        assert EXPECTED_TABLES <= set(inspector.get_table_names())
    finally:
        engine.dispose()


def test_downgrade_base_elimina_todas_las_tablas(migrated_db_url, alembic_config_factory):
    from app.db.session import _build_engine

    command.downgrade(alembic_config_factory(migrated_db_url), "base")

    engine = _build_engine(migrated_db_url)
    try:
        inspector = inspect(engine)
        # `alembic_version` es la tabla de control del propio Alembic: persiste
        # a proposito tras un downgrade a "base" para registrar que no hay
        # ninguna revision aplicada.
        assert set(inspector.get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()


def _crear_persona(session, **overrides):
    defaults = {"nombres": "Nombre", "apellidos": "Apellido"}
    defaults.update(overrides)
    persona = Persona(**defaults)
    session.add(persona)
    session.flush()
    return persona


def test_persona_celular_y_documento_son_nullable_y_no_unicos(db_session):
    p1 = _crear_persona(db_session, celular=None, documento=None)
    p2 = _crear_persona(db_session, celular="0981123456", documento="1234567")
    p3 = _crear_persona(db_session, celular="0981123456", documento="1234567")
    db_session.commit()

    assert p1.celular is None and p1.documento is None
    assert p2.celular == p3.celular
    assert p2.documento == p3.documento


def test_matrimonio_integrante_2_id_es_nullable_para_viudos_consagrados(db_session):
    viudo = _crear_persona(db_session, nombres="Viudo", apellidos="Consagrado")
    matrimonio = Matrimonio(integrante_1_id=viudo.id, integrante_2_id=None, es_consagrado=True)
    db_session.add(matrimonio)
    db_session.commit()

    assert matrimonio.integrante_2_id is None
    assert matrimonio.es_consagrado is True


def test_matrimonio_es_consagrado_es_tri_estado(db_session):
    a = _crear_persona(db_session, nombres="A", apellidos="A")
    b = _crear_persona(db_session, nombres="B", apellidos="B")
    matrimonio_sin_definir = Matrimonio(
        integrante_1_id=a.id, integrante_2_id=b.id, es_consagrado=None
    )
    db_session.add(matrimonio_sin_definir)
    db_session.commit()

    assert matrimonio_sin_definir.es_consagrado is None


def test_matrimonio_no_permite_el_mismo_integrante_dos_veces(db_session):
    persona = _crear_persona(db_session)
    matrimonio = Matrimonio(integrante_1_id=persona.id, integrante_2_id=persona.id)
    db_session.add(matrimonio)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_grupo_nombre_normalizado_es_unico(db_session):
    db_session.add(Grupo(nombre="Circulo 20", nombre_normalizado="CIRCULO 20"))
    db_session.commit()

    db_session.add(Grupo(nombre='Circulo  20 "Katupyry"', nombre_normalizado="CIRCULO 20"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_estado_persona_invalido_es_rechazado_por_check_constraint(db_session):
    persona = _crear_persona(db_session)
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "UPDATE personas SET estado = :estado WHERE id = :id"
            ),
            {"estado": "NO_EXISTE", "id": persona.id},
        )
        db_session.commit()


def _crear_unidad_electoral_y_dependencias(session):
    persona = _crear_persona(session)
    grupo = Grupo(nombre="Circulo 1", nombre_normalizado="CIRCULO 1")
    session.add(grupo)
    session.flush()

    unidad = UnidadElectoral(
        tipo=TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
        referencia_id=grupo.id,
        grupo_id=grupo.id,
    )
    session.add(unidad)

    votacion = Votacion(nombre="Votacion De Prueba", estado=EstadoVotacion.ABIERTA)
    session.add(votacion)
    session.flush()

    opcion = OpcionVoto(votacion_id=votacion.id, nombre="Opcion A")
    session.add(opcion)
    session.flush()

    return persona, unidad, votacion, opcion


def test_voto_unique_constraint_votacion_y_unidad_electoral(db_session):
    persona, unidad, votacion, opcion = _crear_unidad_electoral_y_dependencias(db_session)

    voto_1 = Voto(
        votacion_id=votacion.id,
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
    )
    db_session.add(voto_1)
    db_session.commit()

    voto_2 = Voto(
        votacion_id=votacion.id,
        unidad_electoral_id=unidad.id,
        opcion_id=opcion.id,
        emitido_por_persona_id=persona.id,
    )
    db_session.add(voto_2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_sqlite_aplica_foreign_keys(db_session):
    persona = Persona(nombres="X", apellidos="Y", grupo_id=999999)
    db_session.add(persona)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_incidencia_padron_se_vincula_a_una_importacion(db_session):
    importacion = ImportacionPadron(archivo_origen="padron.xlsx")
    db_session.add(importacion)
    db_session.flush()

    incidencia = IncidenciaPadron(
        tipo=TipoIncidenciaPadron.CELULAR_FALTANTE,
        severidad=SeveridadIncidencia.ALTA,
        importacion_id=importacion.id,
    )
    db_session.add(incidencia)
    db_session.commit()

    assert incidencia.importacion_id == importacion.id


def test_incidencia_padron_importacion_id_es_nullable(db_session):
    incidencia = IncidenciaPadron(
        tipo=TipoIncidenciaPadron.CELULAR_FALTANTE,
        severidad=SeveridadIncidencia.ALTA,
    )
    db_session.add(incidencia)
    db_session.commit()

    assert incidencia.importacion_id is None
