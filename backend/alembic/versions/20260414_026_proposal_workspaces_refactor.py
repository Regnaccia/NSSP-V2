"""proposal_workspaces_refactor - temporary proposal workspaces before export.

Revision ID: 20260414026
Revises: 20260414025
Create Date: 2026-04-14

Adds:
- core_proposal_workspaces
- core_proposal_workspace_rows
- core_production_proposals.workspace_id
- core_production_proposals.workspace_row_id
"""

from alembic import op
import sqlalchemy as sa

revision = "20260414026"
down_revision = "20260414025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_proposal_workspaces",
        sa.Column("workspace_id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("export_batch_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["export_batch_id"],
            ["core_production_proposal_export_batches.batch_id"],
            name="fk_core_proposal_workspaces_export_batch",
        ),
    )
    op.create_index(
        "ix_core_proposal_workspaces_status",
        "core_proposal_workspaces",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_core_proposal_workspaces_expires_at",
        "core_proposal_workspaces",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "core_proposal_workspace_rows",
        sa.Column("row_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("source_candidate_id", sa.String(length=255), nullable=False),
        sa.Column("planning_mode", sa.String(length=64), nullable=True),
        sa.Column("article_code", sa.String(length=64), nullable=False),
        sa.Column("display_label", sa.String(length=255), nullable=False),
        sa.Column("display_description", sa.Text(), nullable=False),
        sa.Column("primary_driver", sa.String(length=32), nullable=True),
        sa.Column("required_qty_minimum", sa.Numeric(14, 4), nullable=False),
        sa.Column("required_qty_total", sa.Numeric(14, 4), nullable=False),
        sa.Column("customer_shortage_qty", sa.Numeric(14, 4), nullable=True),
        sa.Column("stock_replenishment_qty", sa.Numeric(14, 4), nullable=True),
        sa.Column("requested_delivery_date", sa.Date(), nullable=True),
        sa.Column("requested_destination_display", sa.String(length=255), nullable=True),
        sa.Column("active_warning_codes_json", sa.JSON(), nullable=False),
        sa.Column("proposal_logic_key", sa.String(length=64), nullable=False),
        sa.Column("proposal_logic_params_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("proposed_qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("override_qty", sa.Numeric(14, 4), nullable=True),
        sa.Column("override_reason", sa.String(length=500), nullable=True),
        sa.Column("final_qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("order_reference", sa.String(length=64), nullable=True),
        sa.Column("line_reference", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["core_proposal_workspaces.workspace_id"],
            name="fk_core_proposal_workspace_rows_workspace",
        ),
    )
    op.create_index(
        "ix_core_proposal_workspace_rows_workspace_id",
        "core_proposal_workspace_rows",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_core_proposal_workspace_rows_source_candidate_id",
        "core_proposal_workspace_rows",
        ["source_candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_core_proposal_workspace_rows_article_code",
        "core_proposal_workspace_rows",
        ["article_code"],
        unique=False,
    )

    op.add_column(
        "core_production_proposals",
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "core_production_proposals",
        sa.Column("workspace_row_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_core_production_proposals_workspace_id",
        "core_production_proposals",
        "core_proposal_workspaces",
        ["workspace_id"],
        ["workspace_id"],
    )
    op.create_foreign_key(
        "fk_core_production_proposals_workspace_row_id",
        "core_production_proposals",
        "core_proposal_workspace_rows",
        ["workspace_row_id"],
        ["row_id"],
    )
    op.create_index(
        "ix_core_production_proposals_workspace_id",
        "core_production_proposals",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_core_production_proposals_workspace_row_id",
        "core_production_proposals",
        ["workspace_row_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_core_production_proposals_workspace_row_id", table_name="core_production_proposals")
    op.drop_index("ix_core_production_proposals_workspace_id", table_name="core_production_proposals")
    op.drop_constraint("fk_core_production_proposals_workspace_row_id", "core_production_proposals", type_="foreignkey")
    op.drop_constraint("fk_core_production_proposals_workspace_id", "core_production_proposals", type_="foreignkey")
    op.drop_column("core_production_proposals", "workspace_row_id")
    op.drop_column("core_production_proposals", "workspace_id")

    op.drop_index("ix_core_proposal_workspace_rows_article_code", table_name="core_proposal_workspace_rows")
    op.drop_index("ix_core_proposal_workspace_rows_source_candidate_id", table_name="core_proposal_workspace_rows")
    op.drop_index("ix_core_proposal_workspace_rows_workspace_id", table_name="core_proposal_workspace_rows")
    op.drop_table("core_proposal_workspace_rows")

    op.drop_index("ix_core_proposal_workspaces_expires_at", table_name="core_proposal_workspaces")
    op.drop_index("ix_core_proposal_workspaces_status", table_name="core_proposal_workspaces")
    op.drop_table("core_proposal_workspaces")
