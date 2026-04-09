"""core_customer_set_aside

Revision ID: 20260409016
Revises: 20260409015
Create Date: 2026-04-09

Crea la tabella core_customer_set_aside come computed fact canonico della quantita
appartata per cliente (DOC_QTAP). Distinto da core_commitments e core_inventory_positions.
Prima provenienza: customer_order (set_aside_qty da customer_order_lines).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409016"
down_revision = "20260409015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_customer_set_aside",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_code", sa.String(25), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_reference", sa.String(60), nullable=False),
        sa.Column("set_aside_qty", sa.Numeric(18, 5), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_core_customer_set_aside_article_code",
        "core_customer_set_aside",
        ["article_code"],
    )
    op.create_index(
        "ix_core_customer_set_aside_source_type",
        "core_customer_set_aside",
        ["source_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_core_customer_set_aside_source_type", table_name="core_customer_set_aside")
    op.drop_index("ix_core_customer_set_aside_article_code", table_name="core_customer_set_aside")
    op.drop_table("core_customer_set_aside")
