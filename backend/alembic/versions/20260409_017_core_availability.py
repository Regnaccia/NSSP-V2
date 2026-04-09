"""core_availability

Revision ID: 20260409017
Revises: 20260409016
Create Date: 2026-04-09

Crea la tabella core_availability come computed fact canonico della disponibilita libera.
Formula V1: availability_qty = inventory_qty - customer_set_aside_qty - committed_qty
Una riga per article_code (UniqueConstraint).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409017"
down_revision = "20260409016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_availability",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_code", sa.String(25), nullable=False),
        sa.Column("inventory_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("customer_set_aside_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("committed_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("availability_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("article_code", name="uq_core_availability_article_code"),
    )


def downgrade() -> None:
    op.drop_table("core_availability")
