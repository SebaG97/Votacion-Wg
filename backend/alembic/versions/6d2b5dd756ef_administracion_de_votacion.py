"""administracion de votacion: abierta_por, cerrada_por, indice unico parcial

Revision ID: 6d2b5dd756ef
Revises: b02555d5ef5b
Create Date: 2026-08-31 00:00:00.000002

Mision 07: dos gaps que faltaban cerrar sobre `votaciones`.

1. `abierta_por` / `cerrada_por` (String nullable, texto libre que manda el
   cliente admin): no hay sistema de identidad todavia (DEC-021), asi que no
   son FK a un usuario autenticado. El criterio de aceptacion de la mision
   pide que "el cierre registra fecha, hora y usuario"
   (`docs/REGLAS_NEGOCIO.md`).
2. `uq_votacion_estado_abierta`: indice unico parcial sobre `estado`, valido
   solo mientras `estado = 'ABIERTA'`, para reforzar a nivel de base la
   invariante de DEC-018 ("una sola votacion ABIERTA a la vez"). Mismo patron
   de defensa en profundidad que ya usa `votos` (chequeo de servicio +
   constraint de base): `app/services/votacion.py` (`abrir_votacion`)
   verifica primero que no haya otra ABIERTA y ademas envuelve el commit en
   `try/except IntegrityError` por si dos requests pasan el chequeo a la vez.
   `sqlite_where`/`postgresql_where` generan la misma condicion parcial en
   los dos motores.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6d2b5dd756ef'
down_revision: Union[str, Sequence[str], None] = 'b02555d5ef5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("votaciones") as batch_op:
        batch_op.add_column(sa.Column("abierta_por", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("cerrada_por", sa.String(length=255), nullable=True))

    op.create_index(
        "uq_votacion_estado_abierta",
        "votaciones",
        ["estado"],
        unique=True,
        sqlite_where=sa.text("estado = 'ABIERTA'"),
        postgresql_where=sa.text("estado = 'ABIERTA'"),
    )


def downgrade() -> None:
    op.drop_index("uq_votacion_estado_abierta", table_name="votaciones")

    with op.batch_alter_table("votaciones") as batch_op:
        batch_op.drop_column("cerrada_por")
        batch_op.drop_column("abierta_por")
