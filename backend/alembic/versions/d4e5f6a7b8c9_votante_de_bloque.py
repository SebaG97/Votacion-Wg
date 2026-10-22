"""votante de bloque

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-22 00:00:00.000000

DEC-042: `unidades_electorales.votante_matrimonio_id` guarda quien vota un
bloque no consagrado cuando no es el jefe del propio circulo (el educador de
un grupo de postulantes, o el jefe de la parte consagrada de un grupo mixto).
Ademas aplica las reglas sobre el padron ya importado, porque una vez abierta
una votacion el padron no se puede reimportar (DEC-015).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("unidades_electorales") as batch_op:
        batch_op.add_column(sa.Column("votante_matrimonio_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_unidades_electorales_votante_matrimonio",
            "matrimonios",
            ["votante_matrimonio_id"],
            ["id"],
        )

    from app.services.padron.votantes_bloque import aplicar_votantes_de_bloque

    db = Session(bind=op.get_bind())
    aplicar_votantes_de_bloque(db)
    db.flush()


def downgrade() -> None:
    with op.batch_alter_table("unidades_electorales") as batch_op:
        batch_op.drop_constraint("fk_unidades_electorales_votante_matrimonio", type_="foreignkey")
        batch_op.drop_column("votante_matrimonio_id")
