from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class OpcionVoto(Base):
    __tablename__ = "opciones_voto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    votacion_id: Mapped[int] = mapped_column(
        ForeignKey("votaciones.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
