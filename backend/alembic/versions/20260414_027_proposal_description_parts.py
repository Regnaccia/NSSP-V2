"""proposal_description_parts - add description_parts_json snapshot to workspace rows and proposals.

Revision ID: 20260414027
Revises: 20260414026
Create Date: 2026-04-14

Adds:
- core_proposal_workspace_rows.description_parts_json
- core_production_proposals.description_parts_json

Questi campi consentono di derivare lato Core i campi export-preview (TASK-V2-115)
senza dipendere da logica di parsing su display_description.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260414027"
down_revision = "20260414026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_proposal_workspace_rows",
        sa.Column("description_parts_json", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "core_production_proposals",
        sa.Column("description_parts_json", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("core_production_proposals", "description_parts_json")
    op.drop_column("core_proposal_workspace_rows", "description_parts_json")
