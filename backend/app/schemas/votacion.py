"""Schemas de administracion de votacion (Mision 07): crear, cargar opciones,
abrir, cerrar y consultar el estado operativo."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel

from app.models.enums import EstadoVotacion, TipoUnidadElectoral


class VotacionCreateRequest(BaseModel):
    nombre: str


class VotacionResponse(BaseModel):
    id: int
    nombre: str
    estado: EstadoVotacion
    fecha_apertura: dt.datetime | None
    fecha_cierre: dt.datetime | None
    abierta_por: str | None
    cerrada_por: str | None
    resultados_revelados_at: dt.datetime | None

    model_config = {"from_attributes": True}


class OpcionVotoCreateRequest(BaseModel):
    nombre: str
    orden: int | None = None


class OpcionVotoResponse(BaseModel):
    id: int
    votacion_id: int
    nombre: str
    orden: int | None

    model_config = {"from_attributes": True}


class AbrirVotacionRequest(BaseModel):
    usuario: str


class CerrarVotacionRequest(BaseModel):
    usuario: str


class ConteoUnidadesPorEstado(BaseModel):
    habilitada: int
    bloqueada_por_incidencia: int
    pendiente_definicion_postulantes: int
    pendiente_definicion_baja: int


class VotacionEstadoResponse(BaseModel):
    """Estado operativo permitido por REGLAS_NEGOCIO.md mientras la votacion
    esta abierta: nada agrupado por `opcion_id`, eso seria revelar resultados
    antes del cierre."""

    votacion_id: int
    estado: EstadoVotacion
    unidades_por_estado: ConteoUnidadesPorEstado
    votos_emitidos: int
    pendientes: int


class ResultadoOpcion(BaseModel):
    opcion_id: int
    nombre: str
    votos: int
    porcentaje: float


class ResultadoTipoUnidad(BaseModel):
    tipo: TipoUnidadElectoral
    votos_emitidos: int
    unidades_habilitadas: int
    participacion: float | None


class ResultadoGrupo(BaseModel):
    grupo_id: int
    nombre: str
    votos_emitidos: int
    unidades_habilitadas: int
    participacion: float | None


class VotacionResultadosResponse(BaseModel):
    """Resultados por opcion, tipo de unidad electoral y grupo (Mision 08,
    DEC-022). Deliberadamente no cruza grupo x opcion: muchos circulos tienen
    una sola unidad electoral, y ese cruce equivaldria a revelar el voto
    individual de esa unidad."""

    votacion_id: int
    estado: EstadoVotacion
    total_votos: int
    totales_por_opcion: list[ResultadoOpcion]
    totales_por_tipo_unidad: list[ResultadoTipoUnidad]
    totales_por_grupo: list[ResultadoGrupo]
