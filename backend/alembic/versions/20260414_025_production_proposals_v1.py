"""production_proposals_v1 - persistence, article config, and global logic config.

Revision ID: 20260414025
Revises: 20260413024
Create Date: 2026-04-14

Adds:
- core_articolo_config.proposal_logic_key
- core_articolo_config.proposal_logic_article_params_json
- core_proposal_logic_config
- core_production_proposals
- core_production_proposal_export_batches
"""

from alembic import op
import sqlalchemy as sa

revision = "20260414025"
down_revision = "20260413024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_articolo_config",
        sa.Column("proposal_logic_key", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "core_articolo_config",
        sa.Column("proposal_logic_article_params_json", sa.JSON(), nullable=True),
    )

    op.create_table(
        "core_proposal_logic_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("default_logic_key", sa.String(length=64), nullable=False),
        sa.Column("logic_params_by_key_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "core_production_proposal_export_batches",
        sa.Column("batch_id", sa.String(length=64), primary_key=True),
        sa.Column("proposal_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "core_production_proposals",
        sa.Column("proposal_id", sa.Integer(), primary_key=True, autoincrement=True),
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
        sa.Column("workflow_status", sa.String(length=32), nullable=False),
        sa.Column("ode_ref", sa.String(length=64), nullable=False),
        sa.Column("export_batch_id", sa.String(length=64), nullable=True),
        sa.Column("reconciled_production_bucket", sa.String(length=16), nullable=True),
        sa.Column("reconciled_production_id_dettaglio", sa.Integer(), nullable=True),
        sa.Column("order_reference", sa.String(length=64), nullable=True),
        sa.Column("line_reference", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["export_batch_id"],
            ["core_production_proposal_export_batches.batch_id"],
            name="fk_production_proposals_export_batch",
        ),
        sa.UniqueConstraint("ode_ref", name="uq_core_production_proposals_ode_ref"),
    )

    op.create_index(
        "ix_core_production_proposals_source_candidate_id",
        "core_production_proposals",
        ["source_candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_core_production_proposals_article_code",
        "core_production_proposals",
        ["article_code"],
        unique=False,
    )
    op.create_index(
        "ix_core_production_proposals_workflow_status",
        "core_production_proposals",
        ["workflow_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_core_production_proposals_workflow_status", table_name="core_production_proposals")
    op.drop_index("ix_core_production_proposals_article_code", table_name="core_production_proposals")
    op.drop_index("ix_core_production_proposals_source_candidate_id", table_name="core_production_proposals")
    op.drop_table("core_production_proposals")
    op.drop_table("core_production_proposal_export_batches")
    op.drop_table("core_proposal_logic_config")
    op.drop_column("core_articolo_config", "proposal_logic_article_params_json")
    op.drop_column("core_articolo_config", "proposal_logic_key")
