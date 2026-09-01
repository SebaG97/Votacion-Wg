import datetime as dt

from pydantic import BaseModel

from app.models.enums import EstadoImportacion, SeveridadIncidencia, TipoIncidenciaPadron


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
