import datetime as dt

from pydantic import BaseModel

from app.models.enums import EstadoImportacion


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
