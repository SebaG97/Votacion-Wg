from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import TipoUnidadElectoral
from app.models.mixins import TimestampMixin


class UnidadElectoral(TimestampMixin, Base):
    """Entidad que consume el derecho a voto (DEC-003).

    `referencia_id` apunta a `matrimonios.id` cuando `tipo` es
    MATRIMONIO_CONSAGRADO, o a `grupos.id` cuando es BLOQUE_NO_CONSAGRADO.
    No se modela como FK porque la tabla referenciada depende del tipo.
    """

    __tablename__ = "unidades_electorales"
    __table_args__ = (
        UniqueConstraint("tipo", "referencia_id", name="uq_unidad_electoral_tipo_referencia"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[TipoUnidadElectoral] = mapped_column(
        Enum(TipoUnidadElectoral, native_enum=False, create_constraint=True, length=30), nullable=False
    )
    referencia_id: Mapped[int] = mapped_column(Integer, nullable=False)
    grupo_id: Mapped[int | None] = mapped_column(
        ForeignKey("grupos.id"), nullable=True, index=True
    )
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cantidad_personas_control: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
