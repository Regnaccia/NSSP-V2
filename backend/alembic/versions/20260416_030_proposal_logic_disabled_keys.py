"""Add disabled_logic_keys_json to core_proposal_logic_config (TASK-V2-130).

Revision ID: 20260416030
Revises: 20260415029
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260416030"
down_revision = "20260415029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_proposal_logic_config",
        sa.Column(
            "disabled_logic_keys_json",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("core_proposal_logic_config", "disabled_logic_keys_json")
