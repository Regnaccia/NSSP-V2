"""sync layer: sync_destinazioni (TASK-V2-011)

Revision ID: 20260407004
Revises: 20260407003
Create Date: 2026-04-07

Mirror interno di POT_DESTDIV (EasyJob).
Source identity: codice_destinazione (PDES_COD).
Dependency: clienti (CLI_COD mantenuto come campo, no FK hard).
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407004"
down_revision = "20260407003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_destinazioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_destinazione", sa.String(32), nullable=False),
        sa.Column("codice_cli", sa.String(32), nullable=True),
        sa.Column("numero_progressivo_cliente", sa.String(32), nullable=True),
        sa.Column("indirizzo", sa.String(255), nullable=True),
        sa.Column("nazione_codice", sa.String(16), nullable=True),
        sa.Column("citta", sa.String(128), nullable=True),
        sa.Column("provincia", sa.String(4), nullable=True),
        sa.Column("telefono_1", sa.String(64), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codice_destinazione"),
    )


def downgrade() -> None:
    op.drop_table("sync_destinazioni")
