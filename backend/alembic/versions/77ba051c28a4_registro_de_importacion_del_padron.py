"""registro de importacion del padron

Revision ID: 77ba051c28a4
Revises: 19b5c6d93c4b
Create Date: 2026-08-31 00:00:00.000000

Mision 04: agrega `importaciones_padron` (una fila por corrida del
importador, con su resumen de personas/matrimonios/grupos/unidades
electorales creadas e incidencias por severidad) y la FK
`incidencias_padron.importacion_id`, para que cada incidencia quede vinculada
a la corrida que la genero (ver docs/DECISIONES.md DEC-015).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '77ba051c28a4'
down_revision: Union[str, Sequence[str], None] = '19b5c6d93c4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ESTADO_IMPORTACION = sa.Enum(
    "EN_PROCESO", "COMPLETADA", "FALLIDA",
    name="estado_importacion", native_enum=False, create_constraint=True, length=20,
)


def upgrade() -> None:
    op.create_table(
        "importaciones_padron",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("archivo_origen", sa.String(length=500), nullable=False),
        sa.Column("usuario", sa.String(length=255), nullable=True),
        sa.Column("estado", ESTADO_IMPORTACION, nullable=False, server_default="EN_PROCESO"),
        sa.Column("resumen", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )

    with op.batch_alter_table("incidencias_padron") as batch_op:
        batch_op.add_column(sa.Column("importacion_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_incidencias_padron_importacion_id",
            "importaciones_padron",
            ["importacion_id"],
            ["id"],
        )
    op.create_index(
        "ix_incidencias_padron_importacion_id", "incidencias_padron", ["importacion_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_incidencias_padron_importacion_id", table_name="incidencias_padron")
    with op.batch_alter_table("incidencias_padron") as batch_op:
        batch_op.drop_constraint("fk_incidencias_padron_importacion_id", type_="foreignkey")
        batch_op.drop_column("importacion_id")

    op.drop_table("importaciones_padron")
