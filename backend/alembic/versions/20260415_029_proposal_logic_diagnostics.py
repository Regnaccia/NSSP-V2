"""proposal_logic_diagnostics - add requested/effective logic key and fallback reason to workspace rows.

Revision ID: 20260415029
Revises: 20260415028
Create Date: 2026-04-15

Adds to core_proposal_workspace_rows:
- requested_proposal_logic_key (VARCHAR(64) NULL) — logica configurata sull'articolo
- effective_proposal_logic_key (VARCHAR(64) NULL) — logica realmente usata
- proposal_fallback_reason     (VARCHAR(64) NULL) — motivo del fallback; NULL se non c'e fallback

(TASK-V2-124)
"""

from alembic import op
import sqlalchemy as sa

revision = "20260415029"
down_revision = "20260415028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_proposal_workspace_rows",
        sa.Column("requested_proposal_logic_key", sa.String(64), nullable=True),
    )
    op.add_column(
        "core_proposal_workspace_rows",
        sa.Column("effective_proposal_logic_key", sa.String(64), nullable=True),
    )
    op.add_column(
        "core_proposal_workspace_rows",
        sa.Column("proposal_fallback_reason", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_proposal_workspace_rows", "proposal_fallback_reason")
    op.drop_column("core_proposal_workspace_rows", "effective_proposal_logic_key")
    op.drop_column("core_proposal_workspace_rows", "requested_proposal_logic_key")
