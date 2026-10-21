"""Consultas administrativas de padron para el panel (Mision 10, DEC-025):
historial de importaciones, listado filtrable de incidencias, y marcarlas
como revisadas. Mision 12 (DEC-031) agrega `listar_padron`: un visor
filtrable y paginado de personas/matrimonios/grupos/unidades electorales,
deliberadamente sin ningun cruce contra `Voto`.

`resolver_incidencia` setea `resuelto_por`/`resuelto_at` y, desde DEC-039,
reevalua las unidades afectadas: una unidad `BLOQUEADA_POR_INCIDENCIA` sin
ninguna incidencia CRITICA pendiente vuelve a `HABILITADA` (la "resolucion
administrativa" de REGLAS_NEGOCIO.md). Hasta DEC-039 resolver era solo
trazabilidad (DEC-025) y las unidades bloqueadas no tenian salida una vez
congelado el padron. Las unidades de bajas y postulantes (DEC-027/028) nunca
se tocan.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, aliased

from app.models import (
    Grupo,
    ImportacionPadron,
    IncidenciaPadron,
    Matrimonio,
    Persona,
    PersonaEdicion,
    UnidadElectoral,
)
from app.models.enums import EstadoPersona, SeveridadIncidencia, TipoIncidenciaPadron, TipoUnidadElectoral
from app.services.padron.normalizacion import normalizar_celular, texto
from app.models.enums import EstadoUnidadElectoral
from app.services.habilitacion import incidencias_criticas_pendientes


class IncidenciaNoEncontradaError(RuntimeError):
    """La `IncidenciaPadron` indicada no existe."""


class IncidenciaYaResueltaError(RuntimeError):
    """La incidencia ya fue marcada como resuelta."""


class PersonaNoEncontradaError(RuntimeError):
    """La `Persona` indicada no existe."""


class CelularInvalidoError(RuntimeError):
    """El celular ingresado no normaliza a un numero valido."""


class CelularDuplicadoRequiereConfirmacionError(RuntimeError):
    """El celular nuevo ya esta asignado a otra persona de un matrimonio
    distinto (DEC-008). No bloquea -- se reintenta con
    `confirmar_duplicado_celular=True`."""


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


def _unidades_afectadas(
    db: Session, *, persona_ids: set[int], grupo_ids: set[int]
) -> list[UnidadElectoral]:
    """Unidades que una incidencia o una edicion puede estar bloqueando: el
    matrimonio de cada persona y el bloque de cada circulo involucrado.
    `reevaluar_bloqueo` decide despues, con el alcance exacto de DEC-019, si
    cada una sigue bloqueada."""
    matrimonio_ids = {
        m
        for (m,) in db.query(Persona.matrimonio_id).filter(Persona.id.in_(persona_ids)).all()
        if m is not None
    } if persona_ids else set()
    filtros = []
    if matrimonio_ids:
        filtros.append(
            and_(
                UnidadElectoral.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
                UnidadElectoral.referencia_id.in_(matrimonio_ids),
            )
        )
    if grupo_ids:
        filtros.append(
            and_(
                UnidadElectoral.tipo == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
                UnidadElectoral.referencia_id.in_(grupo_ids),
            )
        )
    if not filtros:
        return []
    return db.query(UnidadElectoral).filter(or_(*filtros)).all()


def reevaluar_bloqueo(db: Session, unidades: list[UnidadElectoral]) -> list[UnidadElectoral]:
    """DEC-039: una unidad `BLOQUEADA_POR_INCIDENCIA` vuelve a `HABILITADA`
    cuando ya no le queda ninguna incidencia CRITICA sin resolver (mismo
    alcance que el importador, DEC-019). Nunca toca las unidades de bajas ni
    de postulantes (DEC-027/028): solo mira las bloqueadas por incidencia.
    No hace commit; devuelve las unidades que se habilitaron."""
    habilitadas = []
    for unidad in unidades:
        if unidad.estado != EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value:
            continue
        if not incidencias_criticas_pendientes(db, unidad):
            unidad.estado = EstadoUnidadElectoral.HABILITADA.value
            habilitadas.append(unidad)
    return habilitadas


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
    db.flush()
    # DEC-039 (reemplaza la parte de DEC-025 que decia que resolver no cambia
    # ninguna habilitacion): resolver la ultima incidencia critica de una
    # unidad la vuelve a habilitar. Si el problema era un celular compartido
    # entre matrimonios y nadie lo corrigio, el chequeo en vivo de
    # `celular_compartido_entre_matrimonios` lo sigue frenando igual.
    reevaluar_bloqueo(
        db,
        _unidades_afectadas(
            db,
            persona_ids={incidencia.persona_id} if incidencia.persona_id is not None else set(),
            grupo_ids={incidencia.grupo_id} if incidencia.grupo_id is not None else set(),
        ),
    )
    db.commit()
    db.refresh(incidencia)
    return incidencia


_CAMPOS_EDITABLES = ("nombres", "apellidos", "documento", "celular")


def actualizar_persona(
    db: Session,
    *,
    persona_id: int,
    nombres: str,
    apellidos: str,
    documento: str | None,
    celular: str | None,
    usuario: str,
    confirmar_duplicado_celular: bool = False,
) -> tuple[Persona, list[PersonaEdicion]]:
    """Edita los 4 campos de contacto de una `Persona` del padron (Mision 13,
    DEC-034): `nombres`, `apellidos`, `documento`, `celular`. Deliberadamente
    no toca `estado` ni la consagracion del matrimonio -- eso implicaria
    recalcular/crear unidades electorales, fuera de alcance.

    `celular` se normaliza con la misma funcion que usa el importador
    (`normalizar_celular`). Un celular nuevo que ya pertenece a otra persona
    de un matrimonio distinto no bloquea el guardado (DEC-008: compartir
    celular con el propio conyuge es normal y no genera aviso), pero exige
    `confirmar_duplicado_celular=True` para guardarse -- sin eso, levanta
    `CelularDuplicadoRequiereConfirmacionError` con el detalle de la otra
    persona, para que el llamador pueda avisar antes de confirmar.
    """
    persona = db.get(Persona, persona_id)
    if persona is None:
        raise PersonaNoEncontradaError(f"La persona {persona_id} no existe.")

    nombres_norm = texto(nombres)
    if nombres_norm is None:
        raise ValueError("`nombres` no puede quedar vacio.")
    apellidos_norm = texto(apellidos)
    if apellidos_norm is None:
        raise ValueError("`apellidos` no puede quedar vacio.")
    documento_norm = texto(documento)

    celular_crudo = texto(celular)
    if celular_crudo is None:
        celular_norm = None
    else:
        celular_norm, motivo = normalizar_celular(celular_crudo)
        if celular_norm is None:
            raise CelularInvalidoError(
                f"El celular {celular_crudo!r} no es un numero valido ({motivo})."
            )

    if celular_norm is not None and celular_norm != persona.celular:
        duplicados = (
            db.query(Persona)
            .filter(Persona.celular == celular_norm, Persona.id != persona.id)
            .all()
        )
        duplicados_otro_matrimonio = [
            d
            for d in duplicados
            if not (persona.matrimonio_id is not None and d.matrimonio_id == persona.matrimonio_id)
        ]
        if duplicados_otro_matrimonio and not confirmar_duplicado_celular:
            nombres_duplicados = ", ".join(
                f"{d.nombres} {d.apellidos} (persona {d.id})" for d in duplicados_otro_matrimonio
            )
            raise CelularDuplicadoRequiereConfirmacionError(
                f"El celular {celular_norm} ya esta asignado a: {nombres_duplicados} "
                "(matrimonio distinto). Confirme para guardar el cambio de todos modos."
            )

    valores_nuevos = {
        "nombres": nombres_norm,
        "apellidos": apellidos_norm,
        "documento": documento_norm,
        "celular": celular_norm,
    }

    ediciones: list[PersonaEdicion] = []
    ahora = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    for campo in _CAMPOS_EDITABLES:
        valor_anterior = getattr(persona, campo)
        valor_nuevo = valores_nuevos[campo]
        if valor_anterior == valor_nuevo:
            continue
        edicion = PersonaEdicion(
            persona_id=persona.id,
            campo=campo,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            usuario=usuario,
            fecha=ahora,
        )
        db.add(edicion)
        ediciones.append(edicion)
        setattr(persona, campo, valor_nuevo)

    if celular_norm is not None and persona.matrimonio_id is not None:
        _resolver_sin_celular(db, persona=persona, usuario=usuario, fecha=ahora)

    db.commit()
    db.refresh(persona)
    for edicion in ediciones:
        db.refresh(edicion)
    return persona, ediciones


def _resolver_sin_celular(db: Session, *, persona: Persona, usuario: str, fecha: dt.datetime) -> None:
    """DEC-039: si el matrimonio estaba bloqueado por no tener ningun celular
    valido (DEC-017) y ahora uno de sus integrantes lo tiene, esa incidencia
    queda resuelta (a nombre de quien edito) y la unidad se reevalua."""
    integrantes_ids = [
        pid for (pid,) in db.query(Persona.id).filter(Persona.matrimonio_id == persona.matrimonio_id)
    ]
    pendientes = (
        db.query(IncidenciaPadron)
        .filter(
            IncidenciaPadron.tipo == TipoIncidenciaPadron.MATRIMONIO_SIN_CELULAR_DISPONIBLE,
            IncidenciaPadron.persona_id.in_(integrantes_ids),
            IncidenciaPadron.resuelto_at.is_(None),
        )
        .all()
    )
    if not pendientes:
        return
    for incidencia in pendientes:
        incidencia.resuelto_por = usuario
        incidencia.resuelto_at = fecha
    db.flush()
    reevaluar_bloqueo(
        db, _unidades_afectadas(db, persona_ids=set(integrantes_ids), grupo_ids=set())
    )


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
    persona_id: int | None = None,
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

    if persona_id is not None:
        query = query.filter(Persona.id == persona_id)
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
