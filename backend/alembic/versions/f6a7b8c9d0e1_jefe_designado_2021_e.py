"""DEC-042: los Ayala Lopez son los nuevos jefes de POSTULANTES 2021 "E".

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from alembic import op
from sqlalchemy.orm import Session

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    pass
