"""DEC-042: los Vera Martinez estan habilitados y educan POSTULANTES 2026 D.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""

from alembic import op
from sqlalchemy.orm import Session

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    pass
