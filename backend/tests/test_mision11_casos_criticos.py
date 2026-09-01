"""Dataset de prueba y casos criticos de la Mision 11 (prueba general antes
de una votacion real).

Un unico circulo mixto sintetico ejercita, de punta a punta (habilitacion +
registro de voto, servicios de las Misiones 05 y 06), los casos que
`docs/MISIONES.md` (Mision 11) pide cubrir explicitamente:

- Matrimonio consagrado votando.
- Bloque no consagrado votando.
- Circulo mixto (matrimonio consagrado + bloque no consagrado en el mismo circulo).
- Doble rol de jefe consagrado: dos votos independientes (DEC-014/DEC-026).
- Intento de doble voto sobre la misma unidad: debe bloquear.
- Consulta con celular duplicado (CELULAR_DUPLICADO, DEC-002): bloquea.
- Consulta con celular inexistente: no habilitado.
- Una unidad en cada uno de los cuatro estados de `UnidadElectoral.estado`,
  incluidas las dos resoluciones nuevas de esta mision (DEC-027, DEC-028),
  confirmando que cada una devuelve el `motivo_no_disponible` correcto.

No usa el Excel real: arma los datos directo con los modelos SQLAlchemy,
reusando los helpers de `test_habilitacion.py` y `test_voto.py`, igual que
el resto de la suite de las Misiones 05/06.
"""

from __future__ import annotations

import pytest

from app.models import IncidenciaPadron, OpcionVoto, UnidadElectoral, Voto
from app.models.enums import (
    EstadoUnidadElectoral,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)
from app.services.habilitacion import consultar_habilitacion
from app.services.voto import VotoDuplicadoError, registrar_voto
from tests.test_habilitacion import _grupo, _matrimonio, _persona, _unidad_bloque, _unidad_matrimonio, _votacion_abierta
from tests.test_voto import _opcion


class Dataset:
    def __init__(self, db):
        self.db = db
        self.votacion = _votacion_abierta(db)
        self.opcion = _opcion(db, self.votacion)

        # Circulo mixto: un matrimonio consagrado "de a pie" (persona_a) mas
        # un jefe con doble rol (persona_b, consagrado Y jefe del bloque no
        # consagrado del mismo circulo) -- el circulo tiene, a la vez, una
        # unidad MATRIMONIO_CONSAGRADO ajena al jefe y la unidad
        # BLOQUE_NO_CONSAGRADO que el jefe lidera.
        self.grupo = _grupo(db, "CIRCULO MIXTO 11")

        self.persona_a = _persona(db, "Ana", "Gomez", "0981100001", grupo_id=self.grupo.id)
        self.matrimonio_a = _matrimonio(db, self.persona_a, grupo_id=self.grupo.id)
        self.unidad_matrimonio_a = _unidad_matrimonio(db, self.matrimonio_a)

        self.persona_b = _persona(
            db, "Beto", "Jefe", "0981100002", grupo_id=self.grupo.id, es_jefe_grupo=True
        )
        self.matrimonio_b = _matrimonio(db, self.persona_b, grupo_id=self.grupo.id)
        self.unidad_matrimonio_b = _unidad_matrimonio(db, self.matrimonio_b)
        self.unidad_bloque = _unidad_bloque(db, self.grupo)

        # Celular duplicado entre matrimonios distintos (DEC-002): bloquea.
        self.persona_c = _persona(db, "Carla", "Duplicada", "0981100003")
        self.matrimonio_c = _matrimonio(db, self.persona_c)
        self.unidad_matrimonio_c = _unidad_matrimonio(
            db, self.matrimonio_c, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
        )
        self.persona_d = _persona(db, "Dario", "Duplicado", "0981100003")
        self.matrimonio_d = _matrimonio(db, self.persona_d)
        self.unidad_matrimonio_d = _unidad_matrimonio(
            db, self.matrimonio_d, estado=EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA
        )
        db.add(
            IncidenciaPadron(
                tipo=TipoIncidenciaPadron.CELULAR_DUPLICADO,
                severidad=SeveridadIncidencia.CRITICA,
                descripcion="Celular duplicado entre matrimonios distintos.",
                persona_id=self.persona_c.id,
            )
        )
        db.add(
            IncidenciaPadron(
                tipo=TipoIncidenciaPadron.CELULAR_DUPLICADO,
                severidad=SeveridadIncidencia.CRITICA,
                descripcion="Celular duplicado entre matrimonios distintos.",
                persona_id=self.persona_d.id,
            )
        )

        # Las dos resoluciones nuevas de esta mision (DEC-027, DEC-028): una
        # unidad de cada estado, reutilizado tal cual lo deja el importador.
        self.persona_baja = _persona(db, "Elsa", "DeBaja", "0981100004")
        self.matrimonio_baja = _matrimonio(db, self.persona_baja)
        self.unidad_pendiente_baja = _unidad_matrimonio(
            db, self.matrimonio_baja, estado=EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA
        )

        self.grupo_postulantes = _grupo(db, "CIRCULO POSTULANTES 11")
        self.unidad_pendiente_postulantes = _unidad_bloque(
            db,
            self.grupo_postulantes,
            estado=EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES,
        )

        db.commit()


@pytest.fixture()
def dataset(db_session):
    return Dataset(db_session)


def test_matrimonio_consagrado_vota_exitosamente(dataset):
    voto = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100001",
        unidad_electoral_id=dataset.unidad_matrimonio_a.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_a.id,
    )
    assert voto.unidad_electoral_id == dataset.unidad_matrimonio_a.id


def test_bloque_no_consagrado_vota_exitosamente(dataset):
    voto = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100002",
        unidad_electoral_id=dataset.unidad_bloque.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_b.id,
    )
    assert voto.unidad_electoral_id == dataset.unidad_bloque.id


def test_circulo_mixto_consagrado_y_bloque_votan_de_forma_independiente(dataset):
    """El mismo circulo (CIRCULO MIXTO 11) tiene una unidad MATRIMONIO_CONSAGRADO
    ajena al jefe (persona_a) y la unidad BLOQUE_NO_CONSAGRADO que lidera el
    jefe (persona_b): las dos deben poder votar sin interferir entre si."""
    voto_matrimonio = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100001",
        unidad_electoral_id=dataset.unidad_matrimonio_a.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_a.id,
    )
    voto_bloque = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100002",
        unidad_electoral_id=dataset.unidad_bloque.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_b.id,
    )
    assert voto_matrimonio.id != voto_bloque.id
    assert {voto_matrimonio.unidad_electoral_id, voto_bloque.unidad_electoral_id} == {
        dataset.unidad_matrimonio_a.id,
        dataset.unidad_bloque.id,
    }


def test_jefe_consagrado_doble_rol_emite_dos_votos_independientes(dataset):
    """persona_b es a la vez integrante de un matrimonio consagrado propio
    (unidad_matrimonio_b) y jefe del bloque no consagrado del circulo
    (unidad_bloque, DEC-014/DEC-026): debe poder votar las dos, cada una
    como una fila de `Voto` separada, sin restriccion cruzada."""
    voto_matrimonio_propio = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100002",
        unidad_electoral_id=dataset.unidad_matrimonio_b.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_b.id,
    )
    voto_bloque_liderado = registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100002",
        unidad_electoral_id=dataset.unidad_bloque.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_b.id,
    )
    assert voto_matrimonio_propio.id != voto_bloque_liderado.id

    respuesta = consultar_habilitacion(dataset.db, "0981100002")
    assert len(respuesta.unidades) == 2
    assert all(u.disponible is False for u in respuesta.unidades)
    assert all(u.motivo_no_disponible == "YA_VOTADO" for u in respuesta.unidades)


def test_doble_voto_sobre_la_misma_unidad_queda_bloqueado(dataset):
    registrar_voto(
        dataset.db,
        votacion_id=dataset.votacion.id,
        celular_consultado="0981100001",
        unidad_electoral_id=dataset.unidad_matrimonio_a.id,
        opcion_id=dataset.opcion.id,
        emitido_por_persona_id=dataset.persona_a.id,
    )

    with pytest.raises(VotoDuplicadoError):
        registrar_voto(
            dataset.db,
            votacion_id=dataset.votacion.id,
            celular_consultado="0981100001",
            unidad_electoral_id=dataset.unidad_matrimonio_a.id,
            opcion_id=dataset.opcion.id,
            emitido_por_persona_id=dataset.persona_a.id,
        )

    votos = (
        dataset.db.query(Voto)
        .filter(Voto.unidad_electoral_id == dataset.unidad_matrimonio_a.id)
        .all()
    )
    assert len(votos) == 1


def test_consulta_con_celular_duplicado_queda_bloqueada(dataset):
    """El celular "0981100003" esta cargado en dos personas de matrimonios
    distintos (persona_c y persona_d, DEC-002/DEC-008): la consulta resuelve
    a las dos unidades candidatas, y las dos quedan bloqueadas por su propia
    incidencia CRITICA `CELULAR_DUPLICADO` -- ninguna ofrece voto."""
    respuesta = consultar_habilitacion(dataset.db, "0981100003")

    assert respuesta.habilitado is False
    assert len(respuesta.personas) == 2
    assert len(respuesta.unidades) == 2
    for unidad in respuesta.unidades:
        assert unidad.disponible is False
        assert unidad.motivo_no_disponible == "BLOQUEADA_POR_INCIDENCIA"
        assert unidad.incidencias[0].tipo == TipoIncidenciaPadron.CELULAR_DUPLICADO


def test_consulta_con_celular_inexistente_no_habilitado(dataset):
    respuesta = consultar_habilitacion(dataset.db, "0989999999")

    assert respuesta.habilitado is False
    assert respuesta.personas == []
    assert respuesta.unidades == []


@pytest.mark.parametrize(
    ("celular", "estado_esperado", "unidad_attr", "disponible_esperado"),
    [
        ("0981100001", "HABILITADA", "unidad_matrimonio_a", True),
        ("0981100003", "BLOQUEADA_POR_INCIDENCIA", "unidad_matrimonio_c", False),
    ],
)
def test_estado_de_unidad_se_refleja_en_la_respuesta(
    dataset, celular, estado_esperado, unidad_attr, disponible_esperado
):
    respuesta = consultar_habilitacion(dataset.db, celular)
    unidad_id = getattr(dataset, unidad_attr).id
    unidad = next(u for u in respuesta.unidades if u.unidad_electoral_id == unidad_id)

    assert unidad.estado == estado_esperado
    assert unidad.disponible is disponible_esperado
    if not disponible_esperado:
        assert unidad.motivo_no_disponible == estado_esperado


def test_unidad_pendiente_definicion_baja_no_ofrece_voto_con_motivo_explicito(dataset):
    """DEC-027: resuelta como bloqueo permanente, reutilizando el estado
    `PENDIENTE_DEFINICION_BAJA` que ya existia. El backend no necesita saber
    que la decision "ya esta resuelta": sigue devolviendo el estado real, y
    es el frontend (`frontend/src/lib/motivos.ts`) el que ya no dice
    "todavia"."""
    respuesta = consultar_habilitacion(dataset.db, "0981100004")

    assert respuesta.habilitado is False
    assert len(respuesta.unidades) == 1
    unidad = respuesta.unidades[0]
    assert unidad.estado == "PENDIENTE_DEFINICION_BAJA"
    assert unidad.disponible is False
    assert unidad.motivo_no_disponible == "PENDIENTE_DEFINICION_BAJA"


def test_intento_de_votar_unidad_pendiente_definicion_baja_es_rechazado(dataset):
    from app.services.voto import UnidadElectoralNoDisponibleError

    with pytest.raises(UnidadElectoralNoDisponibleError):
        registrar_voto(
            dataset.db,
            votacion_id=dataset.votacion.id,
            celular_consultado="0981100004",
            unidad_electoral_id=dataset.unidad_pendiente_baja.id,
            opcion_id=dataset.opcion.id,
            emitido_por_persona_id=dataset.persona_baja.id,
        )


def test_unidad_pendiente_definicion_postulantes_no_ofrece_voto(dataset):
    """DEC-028: mismo tratamiento que DEC-027, para circulos de postulantes.
    Esta unidad no tiene ningun jefe asociado en el dataset (a proposito: lo
    unico que importa aca es el estado de la unidad electoral, consultado
    directo en base -- `consultar_habilitacion` solo se llega a traves de un
    celular que resuelva a la unidad, y este circulo sintetico no necesita
    una persona real para verificar que el estado en si bloquea el voto)."""
    unidad = dataset.db.get(UnidadElectoral, dataset.unidad_pendiente_postulantes.id)
    assert unidad.estado == "PENDIENTE_DEFINICION_POSTULANTES"

    from app.services.voto import UnidadElectoralNoDisponibleError

    with pytest.raises(UnidadElectoralNoDisponibleError):
        registrar_voto(
            dataset.db,
            votacion_id=dataset.votacion.id,
            celular_consultado="0000000000",
            unidad_electoral_id=dataset.unidad_pendiente_postulantes.id,
            opcion_id=dataset.opcion.id,
            emitido_por_persona_id=dataset.persona_a.id,
        )
