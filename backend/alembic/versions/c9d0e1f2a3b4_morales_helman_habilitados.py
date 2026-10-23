"""Los Morales Helman (CIRCULO 46) estan habilitados y educan POSTULANTES 2023 F.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
"""

from alembic import op
from sqlalchemy.orm import Session

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    pass
