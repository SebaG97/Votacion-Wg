"""Schemas de la consulta de habilitacion por celular (Mision 05)."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import SeveridadIncidencia, TipoIncidenciaPadron, TipoUnidadElectoral


class HabilitacionConsultaRequest(BaseModel):
    celular: str


class IncidenciaRespuesta(BaseModel):
    tipo: TipoIncidenciaPadron
    severidad: SeveridadIncidencia
    descripcion: str | None

    model_config = {"from_attributes": True}


class PersonaConsultada(BaseModel):
    """Identificacion minima de la persona encontrada por celular.

    Sin celular, documento ni otros datos personales: no hacen falta para que
    el operador reconozca a quien esta consultando.
    """

    persona_id: int
    nombres: str
    apellidos: str

    model_config = {"from_attributes": True}


class UnidadElectoralDisponible(BaseModel):
    """Una unidad electoral candidata para la persona consultada, ya evaluada.

    `motivo_no_disponible` es `None` cuando `disponible` es `True`. Cuando es
    `False`, vale el `estado` de la unidad (`BLOQUEADA_POR_INCIDENCIA`,
    `PENDIENTE_DEFINICION_POSTULANTES`, `PENDIENTE_DEFINICION_BAJA`) o
    `YA_VOTADO` si la unidad esta `HABILITADA` pero ya tiene un voto
    registrado en la votacion abierta.
    """

    unidad_electoral_id: int
    tipo: TipoUnidadElectoral
    descripcion: str | None
    estado: str
    disponible: bool
    motivo_no_disponible: str | None
    incidencias: list[IncidenciaRespuesta] = []


class HabilitacionConsultaResponse(BaseModel):
    celular_normalizado: str | None
    habilitado: bool
    personas: list[PersonaConsultada] = []
    unidades: list[UnidadElectoralDisponible] = []
