"""Aggiunge considera_in_produzione ad articolo_famiglie (TASK-V2-027).

Revision ID: 20260407008
Revises: 20260407007
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = "20260407008"
down_revision = "20260407007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articolo_famiglie",
        sa.Column(
            "considera_in_produzione",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("articolo_famiglie", "considera_in_produzione")
