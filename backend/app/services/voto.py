"""Registro de voto (Mision 06).

Se apoya en el motor de habilitacion de la Mision 05
(`app/services/habilitacion.py`): no reimplementa la resolucion de que
unidades electorales corresponden a un celular, la reusa (`unidades_candidatas`)
para confirmar que el celular declarado en el voto efectivamente resuelve a la
unidad electoral indicada. No calcula conteos ni resultados: eso es la Mision 08.

DEC-014 (doble rol de jefe consagrado) sigue pendiente de negocio: esta mision
no impone ninguna restriccion adicional. Si la misma persona tiene dos unidades
electorales disponibles (su matrimonio y el bloque que lidera), cada una se vota
de forma completamente independiente.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Matrimonio, OpcionVoto, Persona, UnidadElectoral, Votacion, Voto
from app.models.enums import EstadoUnidadElectoral as EstadoUnidad
from app.models.enums import EstadoVotacion, TipoUnidadElectoral
from app.services.habilitacion import unidades_candidatas
from app.services.padron.normalizacion import normalizar_celular


class VotacionNoDisponibleError(RuntimeError):
    """La `Votacion` del path no existe o no esta en estado ABIERTA."""


class UnidadElectoralNoEncontradaError(RuntimeError):
    """La `UnidadElectoral` indicada no existe."""


class UnidadElectoralNoDisponibleError(RuntimeError):
    """La `UnidadElectoral` existe pero su estado no es HABILITADA."""

    def __init__(self, estado_real: str):
        self.estado_real = estado_real
        super().__init__(
            f"La unidad electoral no esta disponible para votar: estado actual "
            f"'{estado_real}'."
        )


class OpcionInvalidaError(RuntimeError):
    """La `OpcionVoto` no existe o no pertenece a la votacion del path."""


class CelularNoResuelveUnidadError(RuntimeError):
    """El `celular_consultado` no resuelve a la `unidad_electoral_id` declarada."""


class PersonaNoAutorizadaError(RuntimeError):
    """`emitido_por_persona_id` no es integrante ni jefe autorizado de la unidad."""


class VotoDuplicadoError(RuntimeError):
    """Ya existe un `Voto` para esa (votacion_id, unidad_electoral_id)."""


def _votacion_abierta(db: Session, votacion_id: int) -> Votacion:
    votacion = db.get(Votacion, votacion_id)
    if votacion is None or votacion.estado != EstadoVotacion.ABIERTA:
        raise VotacionNoDisponibleError(
            f"La votacion {votacion_id} no existe o no esta en estado ABIERTA."
        )
    return votacion


def _unidad_habilitada(db: Session, unidad_electoral_id: int) -> UnidadElectoral:
    unidad = db.get(UnidadElectoral, unidad_electoral_id)
    if unidad is None:
        raise UnidadElectoralNoEncontradaError(
            f"La unidad electoral {unidad_electoral_id} no existe."
        )
    if unidad.estado != EstadoUnidad.HABILITADA.value:
        raise UnidadElectoralNoDisponibleError(unidad.estado)
    return unidad


def _opcion_de_la_votacion(db: Session, votacion_id: int, opcion_id: int) -> OpcionVoto:
    opcion = db.get(OpcionVoto, opcion_id)
    if opcion is None or opcion.votacion_id != votacion_id:
        raise OpcionInvalidaError(
            f"La opcion {opcion_id} no existe o no pertenece a la votacion {votacion_id}."
        )
    return opcion


def _confirmar_celular_resuelve_unidad(
    db: Session, celular_consultado: str, unidad_electoral_id: int
) -> None:
    celular_normalizado, _motivo_rechazo = normalizar_celular(celular_consultado)
    if celular_normalizado is not None:
        personas = db.query(Persona).filter(Persona.celular == celular_normalizado).all()
        if unidad_electoral_id in unidades_candidatas(db, personas):
            return

    raise CelularNoResuelveUnidadError(
        "El celular consultado no resuelve a la unidad electoral indicada."
    )


def _confirmar_persona_autorizada(
    db: Session, unidad: UnidadElectoral, emitido_por_persona_id: int
) -> None:
    if unidad.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO:
        matrimonio = db.get(Matrimonio, unidad.referencia_id)
        autorizada = matrimonio is not None and emitido_por_persona_id in {
            matrimonio.integrante_1_id,
            matrimonio.integrante_2_id,
        }
    else:
        persona = db.get(Persona, emitido_por_persona_id)
        autorizada = (
            persona is not None
            and persona.es_jefe_grupo
            and persona.grupo_id == unidad.referencia_id
        )

    if not autorizada:
        raise PersonaNoAutorizadaError(
            "La persona emisora no esta autorizada para votar por esta unidad electoral."
        )


def _confirmar_sin_voto_previo(db: Session, votacion_id: int, unidad_electoral_id: int) -> None:
    voto_existente = (
        db.query(Voto)
        .filter(Voto.votacion_id == votacion_id, Voto.unidad_electoral_id == unidad_electoral_id)
        .one_or_none()
    )
    if voto_existente is not None:
        raise VotoDuplicadoError(
            "Ya existe un voto registrado para esta unidad electoral en esta votacion."
        )


def registrar_voto(
    db: Session,
    *,
    votacion_id: int,
    celular_consultado: str,
    unidad_electoral_id: int,
    opcion_id: int,
    emitido_por_persona_id: int,
    canal: str | None = None,
) -> Voto:
    _votacion_abierta(db, votacion_id)
    unidad = _unidad_habilitada(db, unidad_electoral_id)
    _opcion_de_la_votacion(db, votacion_id, opcion_id)
    _confirmar_celular_resuelve_unidad(db, celular_consultado, unidad_electoral_id)
    _confirmar_persona_autorizada(db, unidad, emitido_por_persona_id)
    _confirmar_sin_voto_previo(db, votacion_id, unidad_electoral_id)

    celular_normalizado, _ = normalizar_celular(celular_consultado)
    voto = Voto(
        votacion_id=votacion_id,
        unidad_electoral_id=unidad_electoral_id,
        opcion_id=opcion_id,
        emitido_por_persona_id=emitido_por_persona_id,
        celular_consultado=celular_normalizado,
        canal=canal,
    )
    db.add(voto)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise VotoDuplicadoError(
            "Ya existe un voto registrado para esta unidad electoral en esta votacion."
        ) from exc

    db.refresh(voto)
    return voto
