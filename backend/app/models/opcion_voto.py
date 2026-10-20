from sqlalchemy import ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.db.base_class import Base


class OpcionVoto(Base):
    """`foto`/`foto_tipo` (Mision 15, DEC-037): la foto del candidato vive en la
    misma base porque App Platform no conserva archivos subidos entre deploys.
    `foto` es `deferred` para que listar opciones (papeleta, panel, resultados)
    no traiga los bytes de cada imagen; solo los lee el endpoint de la foto."""

    __tablename__ = "opciones_voto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    votacion_id: Mapped[int] = mapped_column(
        ForeignKey("votaciones.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    foto: Mapped[bytes | None] = deferred(mapped_column(LargeBinary, nullable=True))
    foto_tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)

    @property
    def tiene_foto(self) -> bool:
        return self.foto_tipo is not None
