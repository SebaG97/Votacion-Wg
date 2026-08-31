from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import EstadoPersona
from app.models.mixins import TimestampMixin


class Persona(TimestampMixin, Base):
    """Integrante del padron.

    `celular` y `documento` son nullable y sin unicidad en base: 17 personas sin
    celular, 389 sin CI, y pares de conyuges que comparten legitimamente ambos
    datos. La duplicidad real (entre matrimonios distintos) se controla como
    incidencia de importacion, no como restriccion de base (DEC-002, DEC-008,
    PADRON_ANALISIS.md 6.4).
    """

    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombres: Mapped[str] = mapped_column(String(255), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(255), nullable=False)
    celular: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    documento: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    estado: Mapped[EstadoPersona] = mapped_column(
        Enum(EstadoPersona, native_enum=False, create_constraint=True, length=30),
        nullable=False,
        default=EstadoPersona.ACTIVA,
    )
    observacion_baja: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grupo_id: Mapped[int | None] = mapped_column(
        ForeignKey("grupos.id"), nullable=True, index=True
    )
    matrimonio_id: Mapped[int | None] = mapped_column(
        ForeignKey("matrimonios.id"), nullable=True, index=True
    )
    es_jefe_grupo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
