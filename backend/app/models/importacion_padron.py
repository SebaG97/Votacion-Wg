import datetime as dt

from sqlalchemy import JSON, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.models.enums import EstadoImportacion


class ImportacionPadron(Base):
    """Una corrida del importador del padron (Mision 04).

    `usuario` es nullable porque todavia no hay autenticacion (AGENTS.md).
    `resumen` guarda el conteo de personas/matrimonios/grupos/unidades
    electorales creadas y las incidencias por severidad, para que la Mision 05
    y el panel administrativo (Mision 10) puedan mostrarlo sin recalcularlo.
    """

    __tablename__ = "importaciones_padron"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    archivo_origen: Mapped[str] = mapped_column(String(500), nullable=False)
    usuario: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estado: Mapped[EstadoImportacion] = mapped_column(
        Enum(EstadoImportacion, native_enum=False, create_constraint=True, length=20),
        nullable=False,
        default=EstadoImportacion.EN_PROCESO,
    )
    resumen: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
