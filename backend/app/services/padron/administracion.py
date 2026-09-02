"""Consultas administrativas de padron para el panel (Mision 10, DEC-025):
historial de importaciones, listado filtrable de incidencias, y marcarlas
como revisadas. Mision 12 (DEC-031) agrega `listar_padron`: un visor
filtrable y paginado de personas/matrimonios/grupos/unidades electorales,
deliberadamente sin ningun cruce contra `Voto`.

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
from dataclasses import dataclass, field

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, aliased

from app.models import Grupo, ImportacionPadron, IncidenciaPadron, Matrimonio, Persona, UnidadElectoral
from app.models.enums import EstadoPersona, SeveridadIncidencia, TipoIncidenciaPadron, TipoUnidadElectoral


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


@dataclass
class UnidadElectoralResumen:
    id: int
    tipo: TipoUnidadElectoral
    estado: str | None


@dataclass
class PadronPersonaFila:
    """Una fila del visor de padron (Mision 12, DEC-031): datos de la persona,
    su circulo (`Grupo`) y su matrimonio, mas las unidades electorales que le
    corresponden -- puede haber dos si la persona tiene doble rol (jefe de
    grupo consagrado, DEC-020/DEC-026). Nunca incluye nada de `Voto`."""

    id: int
    nombres: str
    apellidos: str
    documento: str | None
    celular: str | None
    estado: EstadoPersona
    grupo_id: int | None
    circulo: str | None
    es_jefe_grupo: bool
    matrimonio_id: int | None
    matrimonio_estado: str | None
    es_consagrado: bool | None
    unidades_electorales: list[UnidadElectoralResumen] = field(default_factory=list)


def listar_padron(
    db: Session,
    *,
    circulo: str | None = None,
    grupo_id: int | None = None,
    estado_persona: EstadoPersona | None = None,
    estado_unidad_electoral: str | None = None,
    tipo_unidad_electoral: TipoUnidadElectoral | None = None,
    nombre: str | None = None,
    documento: str | None = None,
    celular: str | None = None,
    pagina: int = 1,
    tamanio_pagina: int = 50,
) -> tuple[list[PadronPersonaFila], int]:
    """Listado filtrable y paginado de personas del padron, con su circulo
    (`Grupo`), su matrimonio y las unidades electorales que le corresponden.

    Deliberadamente **no** toca `Voto` ni ninguna tabla relacionada (DEC-031):
    es un visor de "quien es quien", no de "que voto cada unidad". Los joins
    a `UnidadElectoral` son por construccion 1:1 desde `Persona` -- el UNIQUE
    `(tipo, referencia_id)` de `UnidadElectoral` mas la condicion de cada
    join garantizan que cada persona aporta a lo sumo una fila por lado
    (matrimonio y bloque), asi que no hay multiplicacion de filas que
    distorsione el conteo total ni la paginacion.
    """
    unidad_matrimonio = aliased(UnidadElectoral)
    unidad_bloque = aliased(UnidadElectoral)

    query = (
        db.query(Persona, Grupo, Matrimonio, unidad_matrimonio, unidad_bloque)
        .outerjoin(Grupo, Persona.grupo_id == Grupo.id)
        .outerjoin(Matrimonio, Persona.matrimonio_id == Matrimonio.id)
        .outerjoin(
            unidad_matrimonio,
            and_(
                unidad_matrimonio.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
                unidad_matrimonio.referencia_id == Persona.matrimonio_id,
            ),
        )
        .outerjoin(
            unidad_bloque,
            and_(
                Persona.es_jefe_grupo.is_(True),
                unidad_bloque.tipo == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
                unidad_bloque.referencia_id == Persona.grupo_id,
            ),
        )
    )

    if circulo:
        query = query.filter(Grupo.nombre.ilike(f"%{circulo}%"))
    if grupo_id is not None:
        query = query.filter(Persona.grupo_id == grupo_id)
    if estado_persona is not None:
        query = query.filter(Persona.estado == estado_persona)
    if nombre:
        patron = f"%{nombre}%"
        query = query.filter(or_(Persona.nombres.ilike(patron), Persona.apellidos.ilike(patron)))
    if documento:
        query = query.filter(Persona.documento.ilike(f"%{documento}%"))
    if celular:
        query = query.filter(Persona.celular.ilike(f"%{celular}%"))
    if tipo_unidad_electoral == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO:
        query = query.filter(unidad_matrimonio.id.isnot(None))
    elif tipo_unidad_electoral == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO:
        query = query.filter(unidad_bloque.id.isnot(None))
    if estado_unidad_electoral:
        query = query.filter(
            or_(
                unidad_matrimonio.estado == estado_unidad_electoral,
                unidad_bloque.estado == estado_unidad_electoral,
            )
        )

    total = query.with_entities(func.count(Persona.id)).scalar() or 0

    pagina = max(pagina, 1)
    tamanio_pagina = min(max(tamanio_pagina, 1), 200)
    filas = (
        query.order_by(Persona.apellidos, Persona.nombres, Persona.id)
        .offset((pagina - 1) * tamanio_pagina)
        .limit(tamanio_pagina)
        .all()
    )

    resultado: list[PadronPersonaFila] = []
    for persona, grupo, matrimonio, u_matrimonio, u_bloque in filas:
        unidades: list[UnidadElectoralResumen] = []
        if u_matrimonio is not None:
            unidades.append(
                UnidadElectoralResumen(id=u_matrimonio.id, tipo=u_matrimonio.tipo, estado=u_matrimonio.estado)
            )
        if u_bloque is not None:
            unidades.append(
                UnidadElectoralResumen(id=u_bloque.id, tipo=u_bloque.tipo, estado=u_bloque.estado)
            )
        resultado.append(
            PadronPersonaFila(
                id=persona.id,
                nombres=persona.nombres,
                apellidos=persona.apellidos,
                documento=persona.documento,
                celular=persona.celular,
                estado=persona.estado,
                grupo_id=persona.grupo_id,
                circulo=grupo.nombre if grupo else None,
                es_jefe_grupo=persona.es_jefe_grupo,
                matrimonio_id=persona.matrimonio_id,
                matrimonio_estado=matrimonio.estado if matrimonio else None,
                es_consagrado=matrimonio.es_consagrado if matrimonio else None,
                unidades_electorales=unidades,
            )
        )

    return resultado, total
