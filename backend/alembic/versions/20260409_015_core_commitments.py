"""core_commitments

Revision ID: 20260409015
Revises: 20260408014
Create Date: 2026-04-09

Crea la tabella core_commitments come computed fact canonico degli impegni attivi per articolo.
Prima provenienza: customer_order (open_qty da customer_order_lines).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409015"
down_revision = "20260408014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_commitments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_code", sa.String(25), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_reference", sa.String(60), nullable=False),
        sa.Column("committed_qty", sa.Numeric(18, 5), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_core_commitments_article_code", "core_commitments", ["article_code"])
    op.create_index("ix_core_commitments_source_type", "core_commitments", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_core_commitments_source_type", table_name="core_commitments")
    op.drop_index("ix_core_commitments_article_code", table_name="core_commitments")
    op.drop_table("core_commitments")
