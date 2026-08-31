"""agrega MATRIMONIO_SIN_CELULAR_DISPONIBLE a tipo_incidencia_padron

Revision ID: b02555d5ef5b
Revises: 77ba051c28a4
Create Date: 2026-08-31 00:00:00.000001

DEC-017: aclaracion textual del dueño del padron sobre DEC-005 -- si ningun
integrante de un matrimonio tiene un celular valido, nadie puede consultar la
habilitacion de esa unidad electoral. `incidencias_padron.tipo` usa
`sa.Enum(..., native_enum=False, create_constraint=True)` (Mision 03), que en
SQLite y en PostgreSQL se traduce a un CHECK constraint con la lista literal
de valores permitidos; esta migracion amplia ese CHECK para admitir el nuevo
valor sin tocar los ~22 existentes.
"""

from typing import Sequence, Union

from alembic import op


revision: str = 'b02555d5ef5b'
down_revision: Union[str, Sequence[str], None] = '77ba051c28a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIPOS_ANTERIORES = [
    "CELULAR_PLACEHOLDER",
    "CELULAR_FORMATO_INVALIDO",
    "CELULAR_FALTANTE",
    "CELULAR_COMPARTIDO_CONYUGES",
    "CELULAR_DUPLICADO",
    "CELULAR_DUPLICADO_EN_LISTADO_JEFES",
    "CELULAR_DISCREPANTE_ENTRE_HOJAS",
    "CI_FALTANTE",
    "CI_COPIADA_ENTRE_CONYUGES",
    "CI_DUPLICADA",
    "MATRIMONIO_SIN_ETIQUETA",
    "MATRIMONIO_INCOMPLETO",
    "CONSAGRACION_INCONSISTENTE",
    "CONSAGRACION_SIN_DEFINIR",
    "NOMBRE_COPIADO_ENTRE_CONYUGES",
    "NOMBRE_NO_ALFABETICO",
    "NOMBRE_DISCREPANTE_ENTRE_HOJAS",
    "CIRCULO_FALTANTE",
    "CIRCULO_ETIQUETA_VARIANTE",
    "CIRCULO_SIN_JEFE",
    "JEFE_SIN_PERSONA_EN_PADRON",
    "JEFE_SOLO_EN_LISTADO_JEFES",
    "JEFE_SOLO_EN_HOJA_PRINCIPAL",
]
TIPO_NUEVO = "MATRIMONIO_SIN_CELULAR_DISPONIBLE"


def _condicion(valores: list[str]) -> str:
    lista = ", ".join(f"'{v}'" for v in valores)
    return f"tipo IN ({lista})"


def upgrade() -> None:
    with op.batch_alter_table("incidencias_padron") as batch_op:
        batch_op.drop_constraint("tipo_incidencia_padron", type_="check")
        batch_op.create_check_constraint(
            "tipo_incidencia_padron", _condicion(TIPOS_ANTERIORES + [TIPO_NUEVO])
        )


def downgrade() -> None:
    with op.batch_alter_table("incidencias_padron") as batch_op:
        batch_op.drop_constraint("tipo_incidencia_padron", type_="check")
        batch_op.create_check_constraint(
            "tipo_incidencia_padron", _condicion(TIPOS_ANTERIORES)
        )
