"""DEC-043: "se fusionaron con el C60" no es una baja.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2

El importador tomaba cualquier observacion como baja. Las personas con una
observacion que no es de baja vuelven a ACTIVA y se recalculan sus unidades.
"""

from alembic import op
from sqlalchemy.orm import Session

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Persona, UnidadElectoral
    from app.models.enums import EstadoPersona, EstadoUnidadElectoral, TipoUnidadElectoral
    from app.services.habilitacion import incidencias_criticas_pendientes
    from app.services.padron.importador import es_observacion_de_baja
    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    matrimonios: set[int] = set()
    for persona in db.query(Persona).filter(Persona.estado == EstadoPersona.BAJA_OBSERVACION):
        if not es_observacion_de_baja(persona.observacion_baja):
            persona.estado = EstadoPersona.ACTIVA
            persona.observacion_baja = None
            if persona.matrimonio_id is not None:
                matrimonios.add(persona.matrimonio_id)
    db.flush()

    for unidad in db.query(UnidadElectoral).filter(
        UnidadElectoral.tipo == TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
        UnidadElectoral.referencia_id.in_(matrimonios),
        UnidadElectoral.estado == EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA.value,
    ):
        unidad.estado = (
            EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value
            if incidencias_criticas_pendientes(db, unidad)
            else EstadoUnidadElectoral.HABILITADA.value
        )
    db.flush()

    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    pass
