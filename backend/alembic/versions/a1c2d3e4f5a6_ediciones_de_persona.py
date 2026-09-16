"""ediciones de persona

Revision ID: a1c2d3e4f5a6
Revises: 6d2b5dd756ef
Create Date: 2026-09-16 00:00:00.000000

Mision 13 (DEC-034): agrega `ediciones_persona`, auditoria campo por campo de
`PATCH /padron/personas/{id}` (nombres, apellidos, documento, celular). A
diferencia del patron `*_por`/`*_at` de un solo actor usado hasta ahora
(`Votacion.abierta_por`, `IncidenciaPadron.resuelto_por`), esta mision pide
"que cambio" (valor anterior/nuevo por campo), asi que cada campo modificado
en una edicion genera su propia fila en vez de una columna sobre `personas`.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '6d2b5dd756ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ediciones_persona",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "persona_id", sa.Integer(), sa.ForeignKey("personas.id"), nullable=False
        ),
        sa.Column("campo", sa.String(length=20), nullable=False),
        sa.Column("valor_anterior", sa.Text(), nullable=True),
        sa.Column("valor_nuevo", sa.Text(), nullable=True),
        sa.Column("usuario", sa.String(length=255), nullable=False),
        sa.Column("fecha", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ediciones_persona_persona_id", "ediciones_persona", ["persona_id"])


def downgrade() -> None:
    op.drop_index("ix_ediciones_persona_persona_id", table_name="ediciones_persona")
    op.drop_table("ediciones_persona")
