import datetime as dt

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import EstadoVotacion
from app.models.mixins import TimestampMixin


class Votacion(TimestampMixin, Base):
    __tablename__ = "votaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoVotacion] = mapped_column(
        Enum(EstadoVotacion, native_enum=False, create_constraint=True, length=30),
        nullable=False,
        default=EstadoVotacion.BORRADOR,
    )
    fecha_apertura: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_cierre: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    resultados_revelados_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime, nullable=True
    )
