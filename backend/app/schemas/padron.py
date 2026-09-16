import datetime as dt

from pydantic import BaseModel

from app.models.enums import (
    EstadoImportacion,
    EstadoPersona,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)


class ImportacionPadronRequest(BaseModel):
    """`excel_path` es opcional: por defecto usa `docs/Padron de ML con Jefes 2026.xlsx`."""

    excel_path: str | None = None
    usuario: str | None = None


class ImportacionPadronResponse(BaseModel):
    id: int
    fecha: dt.datetime
    archivo_origen: str
    usuario: str | None
    estado: EstadoImportacion
    resumen: dict | None
    error: str | None

    model_config = {"from_attributes": True}


class IncidenciaPadronResponse(BaseModel):
    """Fila de `GET /padron/incidencias` (Mision 10, panel administrativo)."""

    id: int
    tipo: TipoIncidenciaPadron
    severidad: SeveridadIncidencia
    descripcion: str | None
    persona_id: int | None
    grupo_id: int | None
    importacion_id: int | None
    resuelto_por: str | None
    resuelto_at: dt.datetime | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ResolverIncidenciaRequest(BaseModel):
    """`usuario` es texto libre, mismo patron que `AbrirVotacionRequest`/
    `CerrarVotacionRequest`: quien tiene el token administrativo declara su
    propio nombre, sin relacion con una identidad autenticada (DEC-021)."""

    usuario: str


class PadronUnidadElectoralResponse(BaseModel):
    id: int
    tipo: TipoUnidadElectoral
    estado: str | None

    model_config = {"from_attributes": True}


class PadronPersonaResponse(BaseModel):
    """Fila de `GET /padron/personas` (Mision 12, DEC-031): datos de padron
    (persona, circulo, matrimonio, unidades electorales) sin ningun dato de
    `Voto`."""

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
    unidades_electorales: list[PadronUnidadElectoralResponse]

    model_config = {"from_attributes": True}


class PadronListadoResponse(BaseModel):
    total: int
    pagina: int
    tamanio_pagina: int
    items: list[PadronPersonaResponse]


class PersonaUpdateRequest(BaseModel):
    """`PATCH /padron/personas/{id}` (Mision 13, DEC-034). Los 4 campos se
    mandan siempre -- el formulario precarga los valores actuales, es
    reemplazo completo de los 4, no un PATCH parcial por campo. `''` en
    `documento`/`celular` significa "sin dato". `usuario` reusa el mismo
    patron que `AbrirVotacionRequest`/`ResolverIncidenciaRequest` (DEC-021):
    texto libre, sin relacion con el token administrativo.
    `confirmar_duplicado_celular` reenvia la misma request tras el aviso no
    bloqueante de celular duplicado entre matrimonios distintos."""

    nombres: str
    apellidos: str
    documento: str | None = None
    celular: str | None = None
    usuario: str
    confirmar_duplicado_celular: bool = False


class PersonaEdicionResponse(BaseModel):
    id: int
    persona_id: int
    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None
    usuario: str
    fecha: dt.datetime

    model_config = {"from_attributes": True}


class PersonaUpdateResponse(BaseModel):
    persona: PadronPersonaResponse
    ediciones: list[PersonaEdicionResponse]
