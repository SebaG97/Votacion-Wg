import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.models.enums import SeveridadIncidencia, TipoIncidenciaPadron


class IncidenciaPadron(Base):
    __tablename__ = "incidencias_padron"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[TipoIncidenciaPadron] = mapped_column(
        Enum(TipoIncidenciaPadron, native_enum=False, create_constraint=True, length=50), nullable=False
    )
    severidad: Mapped[SeveridadIncidencia] = mapped_column(
        Enum(SeveridadIncidencia, native_enum=False, create_constraint=True, length=10), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id"), nullable=True, index=True
    )
    grupo_id: Mapped[int | None] = mapped_column(
        ForeignKey("grupos.id"), nullable=True, index=True
    )
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resuelto_por: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resuelto_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
