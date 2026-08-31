import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class Voto(Base):
    """Voto emitido contra una unidad electoral habilitada.

    La columna Python se llama `metadata_` (mapeada a la columna de base
    `metadata`) porque `metadata` esta reservado en la clase declarativa base
    de SQLAlchemy para la coleccion `MetaData`.
    """

    __tablename__ = "votos"
    __table_args__ = (
        UniqueConstraint(
            "votacion_id", "unidad_electoral_id", name="uq_voto_votacion_unidad_electoral"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    votacion_id: Mapped[int] = mapped_column(
        ForeignKey("votaciones.id"), nullable=False, index=True
    )
    unidad_electoral_id: Mapped[int] = mapped_column(
        ForeignKey("unidades_electorales.id"), nullable=False, index=True
    )
    opcion_id: Mapped[int] = mapped_column(
        ForeignKey("opciones_voto.id"), nullable=False, index=True
    )
    emitido_por_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id"), nullable=True, index=True
    )
    celular_consultado: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_emision: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    canal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
