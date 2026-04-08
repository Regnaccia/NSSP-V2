"""core layer: core_inventory_positions (TASK-V2-037)

Revision ID: 20260408013
Revises: 20260408012
Create Date: 2026-04-08

Computed fact canonica della giacenza netta per articolo.
Formula: on_hand_qty = total_load_qty - total_unload_qty.
Ricostruita dal Core a partire da sync_mag_reale.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260408013"
down_revision = "20260408012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_inventory_positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_code", sa.String(25), nullable=False),
        sa.Column("total_load_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_unload_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("on_hand_qty", sa.Numeric(18, 6), nullable=False),
        sa.Column("movement_count", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_last_movement_date", sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_code", name="uq_core_inventory_positions_article_code"),
    )


def downgrade() -> None:
    op.drop_table("core_inventory_positions")
