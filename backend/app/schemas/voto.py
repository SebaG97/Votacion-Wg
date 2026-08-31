"""Schemas del registro de voto (Mision 06)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class VotoRequest(BaseModel):
    """`emitido_por_persona_id` es obligatorio aca aunque la columna del modelo
    sea nullable: para trazabilidad real el registro siempre tiene que traer
    quien emitio el voto."""

    celular_consultado: str
    unidad_electoral_id: int
    opcion_id: int
    emitido_por_persona_id: int
    canal: str | None = None


class VotoResponse(BaseModel):
    """Sin conteos ni datos agregados por opcion: REGLAS_NEGOCIO.md prohibe
    exponer resultados antes del cierre y esta respuesta no debe ser una
    forma indirecta de filtrarlos."""

    id: int
    votacion_id: int
    unidad_electoral_id: int
    opcion_id: int
    emitido_por_persona_id: int | None
    celular_consultado: str | None
    fecha_emision: dt.datetime
    canal: str | None

    model_config = {"from_attributes": True}
