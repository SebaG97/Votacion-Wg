"""esquema inicial

Revision ID: 19b5c6d93c4b
Revises:
Create Date: 2026-08-31 10:35:46.251127

Crea el modelo persistente inicial de la Mision 03: personas, matrimonios,
grupos, unidades_electorales, votaciones, opciones_voto, votos e
incidencias_padron. Ver docs/MODELO_DATOS_INICIAL.md y
docs/PADRON_ANALISIS.md (seccion 6.4) para el detalle de cada ajuste
(nullability de celular/documento, matrimonios de un solo integrante,
es_consagrado tri-estado, nombre_normalizado de grupo, etc.).

`personas.matrimonio_id` y `matrimonios.integrante_1_id/integrante_2_id` son
una referencia circular entre dos tablas: se crea `personas` primero sin esa
FK, luego `matrimonios`, y al final se agrega la FK a `personas` con
`batch_alter_table` (en SQLite esto recrea la tabla; en PostgreSQL emite un
ALTER TABLE normal).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '19b5c6d93c4b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ESTADO_PERSONA = sa.Enum(
    "ACTIVA", "BAJA_NO_ML", "BAJA_OBSERVACION",
    name="estado_persona", native_enum=False, create_constraint=True, length=30,
)
TIPO_UNIDAD_ELECTORAL = sa.Enum(
    "MATRIMONIO_CONSAGRADO", "BLOQUE_NO_CONSAGRADO",
    name="tipo_unidad_electoral", native_enum=False, create_constraint=True, length=30,
)
ESTADO_VOTACION = sa.Enum(
    "BORRADOR", "ABIERTA", "CERRADA", "RESULTADOS_REVELADOS",
    name="estado_votacion", native_enum=False, create_constraint=True, length=30,
)
SEVERIDAD_INCIDENCIA = sa.Enum(
    "CRITICA", "ALTA", "MEDIA", "BAJA",
    name="severidad_incidencia", native_enum=False, create_constraint=True, length=10,
)
TIPO_INCIDENCIA_PADRON = sa.Enum(
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
    name="tipo_incidencia_padron", native_enum=False, create_constraint=True, length=50,
)


def upgrade() -> None:
    op.create_table(
        "grupos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("nombre_normalizado", sa.String(length=255), nullable=False),
        sa.Column("circulo", sa.String(length=255), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("nombre_normalizado", name="uq_grupo_nombre_normalizado"),
    )

    op.create_table(
        "personas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombres", sa.String(length=255), nullable=False),
        sa.Column("apellidos", sa.String(length=255), nullable=False),
        sa.Column("celular", sa.String(length=10), nullable=True),
        sa.Column("documento", sa.String(length=50), nullable=True),
        sa.Column("estado", ESTADO_PERSONA, nullable=False, server_default="ACTIVA"),
        sa.Column("observacion_baja", sa.String(length=255), nullable=True),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=True),
        sa.Column("matrimonio_id", sa.Integer(), nullable=True),
        sa.Column("es_jefe_grupo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_personas_celular", "personas", ["celular"])
    op.create_index("ix_personas_documento", "personas", ["documento"])
    op.create_index("ix_personas_grupo_id", "personas", ["grupo_id"])
    op.create_index("ix_personas_matrimonio_id", "personas", ["matrimonio_id"])

    op.create_table(
        "matrimonios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_externo", sa.String(length=255), nullable=True),
        sa.Column(
            "integrante_1_id", sa.Integer(), sa.ForeignKey("personas.id"), nullable=False
        ),
        sa.Column(
            "integrante_2_id", sa.Integer(), sa.ForeignKey("personas.id"), nullable=True
        ),
        sa.Column("es_consagrado", sa.Boolean(), nullable=True),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "integrante_2_id IS NULL OR integrante_1_id <> integrante_2_id",
            name="ck_matrimonio_integrantes_distintos",
        ),
    )
    op.create_index("ix_matrimonios_integrante_1_id", "matrimonios", ["integrante_1_id"])
    op.create_index("ix_matrimonios_integrante_2_id", "matrimonios", ["integrante_2_id"])
    op.create_index("ix_matrimonios_grupo_id", "matrimonios", ["grupo_id"])

    with op.batch_alter_table("personas") as batch_op:
        batch_op.create_foreign_key(
            "fk_personas_matrimonio_id", "matrimonios", ["matrimonio_id"], ["id"]
        )

    op.create_table(
        "unidades_electorales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", TIPO_UNIDAD_ELECTORAL, nullable=False),
        sa.Column("referencia_id", sa.Integer(), nullable=False),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=True),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("cantidad_personas_control", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tipo", "referencia_id", name="uq_unidad_electoral_tipo_referencia"
        ),
    )
    op.create_index("ix_unidades_electorales_grupo_id", "unidades_electorales", ["grupo_id"])

    op.create_table(
        "votaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("estado", ESTADO_VOTACION, nullable=False, server_default="BORRADOR"),
        sa.Column("fecha_apertura", sa.DateTime(), nullable=True),
        sa.Column("fecha_cierre", sa.DateTime(), nullable=True),
        sa.Column("resultados_revelados_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "opciones_voto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "votacion_id", sa.Integer(), sa.ForeignKey("votaciones.id"), nullable=False
        ),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_opciones_voto_votacion_id", "opciones_voto", ["votacion_id"])

    op.create_table(
        "votos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "votacion_id", sa.Integer(), sa.ForeignKey("votaciones.id"), nullable=False
        ),
        sa.Column(
            "unidad_electoral_id",
            sa.Integer(),
            sa.ForeignKey("unidades_electorales.id"),
            nullable=False,
        ),
        sa.Column(
            "opcion_id", sa.Integer(), sa.ForeignKey("opciones_voto.id"), nullable=False
        ),
        sa.Column(
            "emitido_por_persona_id",
            sa.Integer(),
            sa.ForeignKey("personas.id"),
            nullable=True,
        ),
        sa.Column("celular_consultado", sa.String(length=10), nullable=True),
        sa.Column(
            "fecha_emision", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("canal", sa.String(length=50), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "votacion_id",
            "unidad_electoral_id",
            name="uq_voto_votacion_unidad_electoral",
        ),
    )
    op.create_index("ix_votos_votacion_id", "votos", ["votacion_id"])
    op.create_index("ix_votos_unidad_electoral_id", "votos", ["unidad_electoral_id"])
    op.create_index("ix_votos_opcion_id", "votos", ["opcion_id"])
    op.create_index("ix_votos_emitido_por_persona_id", "votos", ["emitido_por_persona_id"])

    op.create_table(
        "incidencias_padron",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", TIPO_INCIDENCIA_PADRON, nullable=False),
        sa.Column("severidad", SEVERIDAD_INCIDENCIA, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("personas.id"), nullable=True),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.Column("resuelto_por", sa.String(length=255), nullable=True),
        sa.Column("resuelto_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_incidencias_padron_persona_id", "incidencias_padron", ["persona_id"])
    op.create_index("ix_incidencias_padron_grupo_id", "incidencias_padron", ["grupo_id"])


def downgrade() -> None:
    op.drop_table("incidencias_padron")
    op.drop_table("votos")
    op.drop_table("opciones_voto")
    op.drop_table("votaciones")
    op.drop_table("unidades_electorales")

    with op.batch_alter_table("personas") as batch_op:
        batch_op.drop_constraint("fk_personas_matrimonio_id", type_="foreignkey")

    op.drop_table("matrimonios")
    op.drop_table("personas")
    op.drop_table("grupos")
