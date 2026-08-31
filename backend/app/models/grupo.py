from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Grupo(TimestampMixin, Base):
    """Circulo del padron.

    La relacion grupo -> jefe es 1:N (ver DEC-010 / PADRON_ANALISIS.md 6.4):
    3 circulos tienen dos matrimonios jefe, asi que la jefatura se modela
    desde `Persona.es_jefe_grupo` + `Persona.grupo_id`, no con una FK unica aca.
    """

    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    circulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
