"""Motor de habilitacion por celular (Mision 05).

Dado un celular, resuelve que unidades electorales puede votar la persona o
personas que lo comparten (DEC-008), en que estado real esta cada una y si ya
tiene un voto registrado en la votacion abierta. No registra ningun voto: eso
es la Mision 06.

DEC-018 fija que esta consulta resuelve siempre contra la unica `Votacion` en
estado `ABIERTA`, sin recibir `votacion_id` en la ruta. DEC-019 fija el
alcance de que incidencias CRITICA bloquean cada unidad electoral (y por lo
tanto cuales se muestran como motivo del bloqueo): solo las propias del
matrimonio o del jefe/circulo, nunca las de otro matrimonio del mismo
circulo.
"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import IncidenciaPadron, Matrimonio, Persona, UnidadElectoral, Votacion, Voto
from app.models.enums import EstadoUnidadElectoral as Estado
from app.models.enums import EstadoVotacion, SeveridadIncidencia, TipoUnidadElectoral
from app.schemas.habilitacion import (
    HabilitacionConsultaResponse,
    IncidenciaRespuesta,
    PersonaConsultada,
    UnidadElectoralDisponible,
)
from app.services.padron.normalizacion import normalizar_celular

MOTIVO_YA_VOTADO = "YA_VOTADO"


class NoHayVotacionAbiertaError(RuntimeError):
    """No existe ninguna `Votacion` en estado ABIERTA contra la cual consultar."""


def _votacion_abierta(db: Session) -> Votacion:
    votacion = db.query(Votacion).filter(Votacion.estado == EstadoVotacion.ABIERTA).one_or_none()
    if votacion is None:
        raise NoHayVotacionAbiertaError(
            "No hay ninguna votacion en estado ABIERTA: la consulta de habilitacion no "
            "puede resolverse."
        )
    return votacion


def _incidencias_criticas_matrimonio(db: Session, matrimonio: Matrimonio) -> list[IncidenciaPadron]:
    """Misma condicion de bloqueo que usa el importador (DEC-019) para MATRIMONIO_CONSAGRADO:
    incidencia CRITICA sobre alguno de sus propios integrantes. Una incidencia sobre otro
    matrimonio del mismo circulo no bloquea a este, asi que no cuenta como su causa."""
    integrantes_ids = [matrimonio.integrante_1_id]
    if matrimonio.integrante_2_id is not None:
        integrantes_ids.append(matrimonio.integrante_2_id)

    return (
        db.query(IncidenciaPadron)
        .filter(IncidenciaPadron.severidad == SeveridadIncidencia.CRITICA)
        .filter(IncidenciaPadron.persona_id.in_(integrantes_ids))
        .all()
    )


def _incidencias_criticas_grupo(db: Session, grupo_id: int) -> list[IncidenciaPadron]:
    """Misma condicion de bloqueo que usa el importador (DEC-019) para BLOQUE_NO_CONSAGRADO:
    incidencia CRITICA sobre el circulo en si (`persona_id IS NULL`) o sobre alguno de sus
    jefes. Una incidencia de un matrimonio consagrado puntual del mismo circulo, cuya
    persona no es jefe, no bloquea al bloque."""
    jefes_ids = db.scalars(
        select(Persona.id).where(Persona.grupo_id == grupo_id, Persona.es_jefe_grupo.is_(True))
    ).all()

    filtros = [IncidenciaPadron.persona_id.is_(None)]
    if jefes_ids:
        filtros.append(IncidenciaPadron.persona_id.in_(jefes_ids))

    return (
        db.query(IncidenciaPadron)
        .filter(IncidenciaPadron.severidad == SeveridadIncidencia.CRITICA)
        .filter(IncidenciaPadron.grupo_id == grupo_id)
        .filter(or_(*filtros))
        .all()
    )


def unidades_candidatas(db: Session, personas: list[Persona]) -> dict[int, UnidadElectoral]:
    """Unidades candidatas de todas las personas encontradas, dedupeadas por id.

    Dos conyuges que comparten celular (DEC-008) resuelven al mismo matrimonio
    y por lo tanto a la misma unidad: el dict por id evita ofrecerla dos veces.
    Un jefe consagrado con doble rol (DEC-014) aporta dos unidades distintas
    (su matrimonio y el bloque que lidera), que quedan separadas.

    Publica (sin guion bajo) porque la Mision 06 (`app/services/voto.py`) la
    reusa para confirmar que el celular declarado en el voto efectivamente
    resuelve a la unidad electoral indicada, sin duplicar esta logica.
    """
    unidades: dict[int, UnidadElectoral] = {}
    for persona in personas:
        if persona.matrimonio_id is not None:
            unidad = (
                db.query(UnidadElectoral)
                .filter(
                    UnidadElectoral.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
                    UnidadElectoral.referencia_id == persona.matrimonio_id,
                )
                .one_or_none()
            )
            if unidad is not None:
                unidades[unidad.id] = unidad

        if persona.es_jefe_grupo and persona.grupo_id is not None:
            unidad = (
                db.query(UnidadElectoral)
                .filter(
                    UnidadElectoral.tipo == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
                    UnidadElectoral.referencia_id == persona.grupo_id,
                )
                .one_or_none()
            )
            if unidad is not None:
                unidades[unidad.id] = unidad

    return unidades


def _evaluar_unidad(db: Session, votacion: Votacion, unidad: UnidadElectoral) -> UnidadElectoralDisponible:
    incidencias: list[IncidenciaPadron] = []
    disponible = False
    motivo: str | None = None

    if unidad.estado != Estado.HABILITADA.value:
        motivo = unidad.estado
        if unidad.estado == Estado.BLOQUEADA_POR_INCIDENCIA.value:
            if unidad.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO:
                matrimonio = db.get(Matrimonio, unidad.referencia_id)
                if matrimonio is not None:
                    incidencias = _incidencias_criticas_matrimonio(db, matrimonio)
            else:
                incidencias = _incidencias_criticas_grupo(db, unidad.referencia_id)
    else:
        voto = (
            db.query(Voto)
            .filter(
                Voto.votacion_id == votacion.id,
                Voto.unidad_electoral_id == unidad.id,
            )
            .one_or_none()
        )
        if voto is not None:
            motivo = MOTIVO_YA_VOTADO
        else:
            disponible = True

    return UnidadElectoralDisponible(
        unidad_electoral_id=unidad.id,
        tipo=unidad.tipo,
        descripcion=unidad.descripcion,
        estado=unidad.estado,
        disponible=disponible,
        motivo_no_disponible=motivo,
        incidencias=[IncidenciaRespuesta.model_validate(i) for i in incidencias],
    )


def consultar_habilitacion(db: Session, celular: str) -> HabilitacionConsultaResponse:
    """Resuelve la habilitacion para un celular contra la votacion abierta.

    Levanta `NoHayVotacionAbiertaError` si no hay ninguna votacion ABIERTA
    (DEC-018): eso se resuelve antes de tocar el padron, porque sin votacion
    abierta ninguna unidad puede ofrecerse para votar.
    """
    votacion = _votacion_abierta(db)

    celular_normalizado, _motivo_rechazo = normalizar_celular(celular)
    if celular_normalizado is None:
        return HabilitacionConsultaResponse(celular_normalizado=None, habilitado=False)

    personas = (
        db.query(Persona)
        .filter(Persona.celular == celular_normalizado)
        .order_by(Persona.id)
        .all()
    )
    if not personas:
        return HabilitacionConsultaResponse(
            celular_normalizado=celular_normalizado, habilitado=False
        )

    candidatas = unidades_candidatas(db, personas)
    unidades_respuesta = [
        _evaluar_unidad(db, votacion, unidad)
        for unidad in sorted(candidatas.values(), key=lambda u: u.id)
    ]

    return HabilitacionConsultaResponse(
        celular_normalizado=celular_normalizado,
        habilitado=any(u.disponible for u in unidades_respuesta),
        personas=[
            PersonaConsultada(persona_id=p.id, nombres=p.nombres, apellidos=p.apellidos)
            for p in personas
        ],
        unidades=unidades_respuesta,
    )
