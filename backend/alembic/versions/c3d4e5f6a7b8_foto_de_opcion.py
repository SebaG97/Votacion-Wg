"""foto de opcion

Revision ID: c3d4e5f6a7b8
Revises: a1c2d3e4f5a6
Create Date: 2026-10-20 00:00:00.000000

Mision 15 (DEC-037): foto del candidato guardada en `opciones_voto` (bytes y
tipo MIME). Ambas columnas son nullable: las opciones existentes quedan sin
foto y la papeleta sigue mostrando solo el nombre.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("opciones_voto") as batch_op:
        batch_op.add_column(sa.Column("foto", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("foto_tipo", sa.String(length=30), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("opciones_voto") as batch_op:
        batch_op.drop_column("foto_tipo")
        batch_op.drop_column("foto")
