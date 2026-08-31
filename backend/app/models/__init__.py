"""Modelos SQLAlchemy. Importar este paquete registra todas las tablas en Base.metadata."""

from app.db.base_class import Base
from app.models.grupo import Grupo
from app.models.incidencia_padron import IncidenciaPadron
from app.models.matrimonio import Matrimonio
from app.models.opcion_voto import OpcionVoto
from app.models.persona import Persona
from app.models.unidad_electoral import UnidadElectoral
from app.models.votacion import Votacion
from app.models.voto import Voto

__all__ = [
    "Base",
    "Grupo",
    "IncidenciaPadron",
    "Matrimonio",
    "OpcionVoto",
    "Persona",
    "UnidadElectoral",
    "Votacion",
    "Voto",
]

