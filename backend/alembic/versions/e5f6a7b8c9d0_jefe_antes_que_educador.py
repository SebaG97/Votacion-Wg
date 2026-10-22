"""DEC-042: con jefe activo el bloque lo vota el jefe, no el educador.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""

from alembic import op
from sqlalchemy.orm import Session

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    pass
