import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class PersonaEdicion(Base):
    """Auditoria campo por campo de `PATCH /padron/personas/{id}` (Mision 13,
    DEC-034). A diferencia del patron `*_por`/`*_at` de un solo actor usado en
    el resto del proyecto (`Votacion.abierta_por`, `IncidenciaPadron.resuelto_por`),
    aca hace falta "que cambio" (valor anterior/nuevo), asi que cada campo
    modificado en una edicion genera su propia fila.
    """

    __tablename__ = "ediciones_persona"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"), nullable=False, index=True)
    campo: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
