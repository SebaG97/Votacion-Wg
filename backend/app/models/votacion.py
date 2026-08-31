import datetime as dt

from sqlalchemy import DateTime, Enum, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import EstadoVotacion
from app.models.mixins import TimestampMixin


class Votacion(TimestampMixin, Base):
    """`uq_votacion_estado_abierta` refuerza a nivel de base la invariante de
    DEC-018 ("una sola votacion ABIERTA a la vez"): es un indice unico parcial
    sobre `estado`, valido solo mientras `estado = 'ABIERTA'`, para que dos
    filas ABIERTA nunca puedan coexistir aunque el chequeo de servicio en
    `app/services/votacion.py` (`abrir_votacion`) se salte por una carrera.
    """

    __tablename__ = "votaciones"
    __table_args__ = (
        Index(
            "uq_votacion_estado_abierta",
            "estado",
            unique=True,
            sqlite_where=text("estado = 'ABIERTA'"),
            postgresql_where=text("estado = 'ABIERTA'"),
        ),
    )

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
    abierta_por: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cerrada_por: Mapped[str | None] = mapped_column(String(255), nullable=True)
