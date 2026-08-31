"""Administracion de votacion: crear, cargar opciones, abrir, cerrar y
consultar el estado operativo (Mision 07).

Cierra dos gaps que quedaban abiertos hasta esta mision: no existia forma de
crear una `Votacion` ni sus `OpcionVoto` por endpoint (todo se armaba por
ORM en tests), y el modelo no registraba quien abrio o cerro la votacion
(`Votacion.abierta_por` / `cerrada_por`, agregados en esta misma mision).

DEC-018 asumia que "abrir una votacion" era un UPDATE manual porque esta
mision todavia no existia; a partir de aca `abrir_votacion` es el unico
camino soportado para pasar una `Votacion` a ABIERTA y el que garantiza que
nunca haya dos a la vez, con el mismo patron de defensa en profundidad que
`app/services/voto.py`: chequeo de servicio (`_confirmar_sin_otra_abierta`)
mas el indice unico parcial `uq_votacion_estado_abierta`
(`app/models/votacion.py`) como respaldo ante una carrera.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Grupo, OpcionVoto, UnidadElectoral, Votacion, Voto
from app.models.enums import EstadoUnidadElectoral, EstadoVotacion, TipoUnidadElectoral


class VotacionNoEncontradaError(RuntimeError):
    """La `Votacion` indicada no existe."""


class VotacionNoEsBorradorError(RuntimeError):
    """La operacion exige `estado == BORRADOR` y la votacion ya avanzo."""


class VotacionSinOpcionesError(RuntimeError):
    """No se puede abrir una votacion sin al menos una `OpcionVoto` cargada."""


class OtraVotacionAbiertaError(RuntimeError):
    """Ya existe otra `Votacion` en estado ABIERTA (DEC-018)."""


class VotacionNoAbiertaError(RuntimeError):
    """La operacion exige `estado == ABIERTA` y la votacion no lo esta."""


class VotacionNoCerradaError(RuntimeError):
    """`revelar_resultados` exige `estado == CERRADA` y la votacion no lo esta."""


class ResultadosYaReveladosError(RuntimeError):
    """La votacion ya paso por `revelar_resultados` (estado RESULTADOS_REVELADOS)."""


class ResultadosBloqueadosError(RuntimeError):
    """Los resultados solo se pueden consultar con `estado` CERRADA o RESULTADOS_REVELADOS
    (DEC-022): mientras la votacion esta en BORRADOR o ABIERTA, REGLAS_NEGOCIO.md prohibe
    exponer ningun conteo por opcion."""


def _obtener_votacion(db: Session, votacion_id: int) -> Votacion:
    votacion = db.get(Votacion, votacion_id)
    if votacion is None:
        raise VotacionNoEncontradaError(f"La votacion {votacion_id} no existe.")
    return votacion


def crear_votacion(db: Session, *, nombre: str) -> Votacion:
    votacion = Votacion(nombre=nombre, estado=EstadoVotacion.BORRADOR)
    db.add(votacion)
    db.commit()
    db.refresh(votacion)
    return votacion


def agregar_opcion(
    db: Session, *, votacion_id: int, nombre: str, orden: int | None = None
) -> OpcionVoto:
    votacion = _obtener_votacion(db, votacion_id)
    if votacion.estado != EstadoVotacion.BORRADOR:
        raise VotacionNoEsBorradorError(
            f"La votacion {votacion_id} ya no esta en BORRADOR (estado actual "
            f"'{votacion.estado.value}'): no se pueden agregar ni editar opciones."
        )

    opcion = OpcionVoto(votacion_id=votacion_id, nombre=nombre, orden=orden)
    db.add(opcion)
    db.commit()
    db.refresh(opcion)
    return opcion


def listar_opciones(db: Session, votacion_id: int) -> list[OpcionVoto]:
    _obtener_votacion(db, votacion_id)
    return (
        db.query(OpcionVoto)
        .filter(OpcionVoto.votacion_id == votacion_id)
        .order_by(OpcionVoto.orden.is_(None), OpcionVoto.orden, OpcionVoto.id)
        .all()
    )


def _confirmar_sin_otra_abierta(db: Session, votacion_id: int) -> None:
    otra = (
        db.query(Votacion)
        .filter(Votacion.estado == EstadoVotacion.ABIERTA, Votacion.id != votacion_id)
        .first()
    )
    if otra is not None:
        raise OtraVotacionAbiertaError(
            f"Ya existe otra votacion ABIERTA (id={otra.id}): no se puede abrir una segunda."
        )


def abrir_votacion(db: Session, *, votacion_id: int, usuario: str) -> Votacion:
    votacion = _obtener_votacion(db, votacion_id)
    if votacion.estado != EstadoVotacion.BORRADOR:
        raise VotacionNoEsBorradorError(
            f"La votacion {votacion_id} no esta en BORRADOR (estado actual "
            f"'{votacion.estado.value}'): no se puede abrir."
        )

    tiene_opciones = (
        db.query(OpcionVoto.id).filter(OpcionVoto.votacion_id == votacion_id).first()
        is not None
    )
    if not tiene_opciones:
        raise VotacionSinOpcionesError(
            f"La votacion {votacion_id} no tiene ninguna opcion cargada: no se puede abrir."
        )

    _confirmar_sin_otra_abierta(db, votacion_id)

    votacion.estado = EstadoVotacion.ABIERTA
    votacion.fecha_apertura = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    votacion.abierta_por = usuario
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise OtraVotacionAbiertaError(
            "Ya existe otra votacion ABIERTA: no se puede abrir una segunda."
        ) from exc

    db.refresh(votacion)
    return votacion


def cerrar_votacion(db: Session, *, votacion_id: int, usuario: str) -> Votacion:
    votacion = _obtener_votacion(db, votacion_id)
    if votacion.estado != EstadoVotacion.ABIERTA:
        raise VotacionNoAbiertaError(
            f"La votacion {votacion_id} no esta ABIERTA (estado actual "
            f"'{votacion.estado.value}'): no se puede cerrar."
        )

    votacion.estado = EstadoVotacion.CERRADA
    votacion.fecha_cierre = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    votacion.cerrada_por = usuario
    db.commit()
    db.refresh(votacion)
    return votacion


def obtener_estado_operativo(db: Session, votacion_id: int) -> dict:
    """Estado operativo permitido por REGLAS_NEGOCIO.md mientras la votacion
    esta abierta (o en cualquier estado, para uso administrativo): nunca
    incluye nada agrupado por `opcion_id`, eso es revelar resultados antes
    del cierre y esta mision no lo implementa (Mision 08)."""
    votacion = _obtener_votacion(db, votacion_id)

    conteos = {estado.value: 0 for estado in EstadoUnidadElectoral}
    filas = (
        db.query(UnidadElectoral.estado, func.count(UnidadElectoral.id))
        .group_by(UnidadElectoral.estado)
        .all()
    )
    for estado_unidad, cantidad in filas:
        if estado_unidad in conteos:
            conteos[estado_unidad] = cantidad

    votos_emitidos = (
        db.query(func.count(Voto.id)).filter(Voto.votacion_id == votacion_id).scalar()
    )
    pendientes = conteos[EstadoUnidadElectoral.HABILITADA.value] - votos_emitidos

    return {
        "votacion_id": votacion.id,
        "estado": votacion.estado,
        "unidades_por_estado": {
            "habilitada": conteos[EstadoUnidadElectoral.HABILITADA.value],
            "bloqueada_por_incidencia": conteos[
                EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value
            ],
            "pendiente_definicion_postulantes": conteos[
                EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES.value
            ],
            "pendiente_definicion_baja": conteos[
                EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA.value
            ],
        },
        "votos_emitidos": votos_emitidos,
        "pendientes": pendientes,
    }


def revelar_resultados(db: Session, *, votacion_id: int) -> Votacion:
    """Hito formal de DEC-022: pasa la votacion de CERRADA a RESULTADOS_REVELADOS
    y sella `resultados_revelados_at`. No cambia que devuelve `obtener_resultados`
    (ya funciona en CERRADA); es la marca que distingue "cerrada pero todavia no
    comunicada" de "ya anunciada" para uso administrativo futuro."""
    votacion = _obtener_votacion(db, votacion_id)
    if votacion.estado == EstadoVotacion.RESULTADOS_REVELADOS:
        raise ResultadosYaReveladosError(
            f"La votacion {votacion_id} ya fueron revelados el "
            f"{votacion.resultados_revelados_at}."
        )
    if votacion.estado != EstadoVotacion.CERRADA:
        raise VotacionNoCerradaError(
            f"La votacion {votacion_id} no esta CERRADA (estado actual "
            f"'{votacion.estado.value}'): no se pueden revelar resultados."
        )

    votacion.estado = EstadoVotacion.RESULTADOS_REVELADOS
    votacion.resultados_revelados_at = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(votacion)
    return votacion


def obtener_resultados(db: Session, votacion_id: int) -> dict:
    """Resultados por opcion, por tipo de unidad electoral y por grupo (DEC-022).

    Solo disponible con `estado` CERRADA o RESULTADOS_REVELADOS -- con
    BORRADOR o ABIERTA se rechaza antes de calcular nada. Los conteos se
    calculan siempre a partir de las filas de `Voto` de esta votacion, nunca
    de `UnidadElectoral.estado` (ese campo es de elegibilidad, no de
    resultados): las "unidades habilitadas" que se reportan como denominador
    de participacion son un conteo aparte, sobre el padron actual.

    No se cruza grupo x opcion (DEC-022): muchos circulos tienen una sola
    unidad electoral, asi que ese cruce equivaldria a revelar el voto
    individual de esa unidad.
    """
    votacion = _obtener_votacion(db, votacion_id)
    if votacion.estado not in (EstadoVotacion.CERRADA, EstadoVotacion.RESULTADOS_REVELADOS):
        raise ResultadosBloqueadosError(
            f"Resultados bloqueados hasta el cierre (estado actual "
            f"'{votacion.estado.value}')."
        )

    total_votos = (
        db.query(func.count(Voto.id)).filter(Voto.votacion_id == votacion_id).scalar()
    )

    opciones = listar_opciones(db, votacion_id)
    votos_por_opcion = dict(
        db.query(Voto.opcion_id, func.count(Voto.id))
        .filter(Voto.votacion_id == votacion_id)
        .group_by(Voto.opcion_id)
        .all()
    )
    totales_por_opcion = [
        {
            "opcion_id": opcion.id,
            "nombre": opcion.nombre,
            "votos": votos_por_opcion.get(opcion.id, 0),
            "porcentaje": (
                votos_por_opcion.get(opcion.id, 0) / total_votos * 100 if total_votos else 0.0
            ),
        }
        for opcion in opciones
    ]

    votos_por_tipo = dict(
        db.query(UnidadElectoral.tipo, func.count(Voto.id))
        .join(Voto, Voto.unidad_electoral_id == UnidadElectoral.id)
        .filter(Voto.votacion_id == votacion_id)
        .group_by(UnidadElectoral.tipo)
        .all()
    )
    habilitadas_por_tipo = dict(
        db.query(UnidadElectoral.tipo, func.count(UnidadElectoral.id))
        .filter(UnidadElectoral.estado == EstadoUnidadElectoral.HABILITADA.value)
        .group_by(UnidadElectoral.tipo)
        .all()
    )
    totales_por_tipo_unidad = []
    for tipo in TipoUnidadElectoral:
        emitidos = votos_por_tipo.get(tipo, 0)
        habilitadas = habilitadas_por_tipo.get(tipo, 0)
        totales_por_tipo_unidad.append(
            {
                "tipo": tipo,
                "votos_emitidos": emitidos,
                "unidades_habilitadas": habilitadas,
                "participacion": (emitidos / habilitadas) if habilitadas else None,
            }
        )

    votos_por_grupo = dict(
        db.query(UnidadElectoral.grupo_id, func.count(Voto.id))
        .join(Voto, Voto.unidad_electoral_id == UnidadElectoral.id)
        .filter(Voto.votacion_id == votacion_id)
        .group_by(UnidadElectoral.grupo_id)
        .all()
    )
    habilitadas_por_grupo = dict(
        db.query(UnidadElectoral.grupo_id, func.count(UnidadElectoral.id))
        .filter(UnidadElectoral.estado == EstadoUnidadElectoral.HABILITADA.value)
        .group_by(UnidadElectoral.grupo_id)
        .all()
    )
    totales_por_grupo = []
    for grupo in db.query(Grupo).order_by(Grupo.nombre).all():
        emitidos = votos_por_grupo.get(grupo.id, 0)
        habilitadas = habilitadas_por_grupo.get(grupo.id, 0)
        totales_por_grupo.append(
            {
                "grupo_id": grupo.id,
                "nombre": grupo.nombre,
                "votos_emitidos": emitidos,
                "unidades_habilitadas": habilitadas,
                "participacion": (emitidos / habilitadas) if habilitadas else None,
            }
        )

    return {
        "votacion_id": votacion.id,
        "estado": votacion.estado,
        "total_votos": total_votos,
        "totales_por_opcion": totales_por_opcion,
        "totales_por_tipo_unidad": totales_por_tipo_unidad,
        "totales_por_grupo": totales_por_grupo,
    }
