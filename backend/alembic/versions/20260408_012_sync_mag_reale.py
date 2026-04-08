"""sync layer: sync_mag_reale (TASK-V2-036)

Revision ID: 20260408012
Revises: 20260407011
Create Date: 2026-04-08

Mirror interno di MAG_REALE (EasyJob).
Source identity: id_movimento (ID_MAGREALE).
Alignment: append_only + cursor.
Delete handling: no_delete_handling.
Dependencies: nessuna.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260408012"
down_revision = "20260407011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_mag_reale",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_movimento", sa.Integer(), nullable=False),
        sa.Column("codice_articolo", sa.String(25), nullable=True),
        sa.Column("quantita_caricata", sa.Numeric(18, 6), nullable=True),
        sa.Column("quantita_scaricata", sa.Numeric(18, 6), nullable=True),
        sa.Column("causale_movimento_codice", sa.String(6), nullable=True),
        sa.Column("data_movimento", sa.DateTime(timezone=False), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_movimento", name="uq_sync_mag_reale_id_movimento"),
    )


def downgrade() -> None:
    op.drop_table("sync_mag_reale")
