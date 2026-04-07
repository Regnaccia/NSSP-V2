"""sync layer: sync_clienti, sync_run_log, sync_entity_state

Revision ID: 20260407002
Revises: 20260407001
Create Date: 2026-04-07

Slice sync clienti (DL-ARCH-V2-009):
- sync_clienti:       mirror interno di ANACLI (EasyJob) — source identity: codice_cli
- sync_run_log:       metadati di ogni esecuzione di sync
- sync_entity_state:  freshness anchor per entita (last_success_at)
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407002"
down_revision = "20260407001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_clienti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_cli", sa.String(32), nullable=False),
        sa.Column("ragione_sociale", sa.String(255), nullable=False, server_default=""),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codice_cli"),
    )

    op.create_table(
        "sync_run_log",
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("entity_code", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("rows_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
    )

    op.create_table(
        "sync_entity_state",
        sa.Column("entity_code", sa.String(64), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(16), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("entity_code"),
    )


def downgrade() -> None:
    op.drop_table("sync_entity_state")
    op.drop_table("sync_run_log")
    op.drop_table("sync_clienti")
