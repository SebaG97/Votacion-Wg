from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Matrimonio(TimestampMixin, Base):
    """Matrimonio del padron.

    `integrante_2_id` es nullable: hay 29 matrimonios de un solo integrante,
    22 de ellos viudos consagrados que conservan el voto (DEC-011).

    `es_consagrado` es un booleano nullable (tri-estado): 19 matrimonios no
    tienen ninguna marca en el Excel y forzarlos a False los excluiria
    silenciosamente del padron (PADRON_ANALISIS.md 6.4).
    """

    __tablename__ = "matrimonios"
    __table_args__ = (
        CheckConstraint(
            "integrante_2_id IS NULL OR integrante_1_id <> integrante_2_id",
            name="ck_matrimonio_integrantes_distintos",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_externo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    integrante_1_id: Mapped[int] = mapped_column(
        ForeignKey("personas.id"), nullable=False, index=True
    )
    integrante_2_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id"), nullable=True, index=True
    )
    es_consagrado: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grupo_id: Mapped[int | None] = mapped_column(
        ForeignKey("grupos.id"), nullable=True, index=True
    )
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
