"""Consultas administrativas de padron para el panel (Mision 10, DEC-025):
historial de importaciones, listado filtrable de incidencias, y marcarlas
como revisadas.

`resolver_incidencia` es trazabilidad administrativa pura: setea
`resuelto_por`/`resuelto_at` (columnas de `IncidenciaPadron` que existen desde
la Mision 03 pero que hasta esta mision nunca se escribian) y nunca toca
`UnidadElectoral.estado`. Recalcular la habilitacion de una unidad
automaticamente exigiria resolver antes DEC-012 (bajas), DEC-013 (circulos de
postulantes) y DEC-014 (doble rol de jefes consagrados), las tres todavia
pendientes de negocio.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.models import ImportacionPadron, IncidenciaPadron
from app.models.enums import SeveridadIncidencia, TipoIncidenciaPadron


class IncidenciaNoEncontradaError(RuntimeError):
    """La `IncidenciaPadron` indicada no existe."""


class IncidenciaYaResueltaError(RuntimeError):
    """La incidencia ya fue marcada como resuelta."""


def listar_importaciones(db: Session) -> list[ImportacionPadron]:
    """Mas nueva primero. Desempata por `id` (no solo por `fecha`): en SQLite
    `func.now()` tiene resolucion de segundo, asi que dos importaciones
    corridas dentro del mismo segundo comparten `fecha`."""
    return (
        db.query(ImportacionPadron)
        .order_by(ImportacionPadron.fecha.desc(), ImportacionPadron.id.desc())
        .all()
    )


def listar_incidencias(
    db: Session,
    *,
    severidad: SeveridadIncidencia | None = None,
    tipo: TipoIncidenciaPadron | None = None,
    resuelta: bool | None = None,
) -> list[IncidenciaPadron]:
    query = db.query(IncidenciaPadron)
    if severidad is not None:
        query = query.filter(IncidenciaPadron.severidad == severidad)
    if tipo is not None:
        query = query.filter(IncidenciaPadron.tipo == tipo)
    if resuelta is True:
        query = query.filter(IncidenciaPadron.resuelto_at.isnot(None))
    elif resuelta is False:
        query = query.filter(IncidenciaPadron.resuelto_at.is_(None))
    return query.order_by(IncidenciaPadron.id).all()


def resolver_incidencia(db: Session, *, incidencia_id: int, usuario: str) -> IncidenciaPadron:
    incidencia = db.get(IncidenciaPadron, incidencia_id)
    if incidencia is None:
        raise IncidenciaNoEncontradaError(f"La incidencia {incidencia_id} no existe.")
    if incidencia.resuelto_at is not None:
        raise IncidenciaYaResueltaError(
            f"La incidencia {incidencia_id} ya fue resuelta por "
            f"{incidencia.resuelto_por!r} el {incidencia.resuelto_at}."
        )

    incidencia.resuelto_por = usuario
    incidencia.resuelto_at = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(incidencia)
    return incidencia
