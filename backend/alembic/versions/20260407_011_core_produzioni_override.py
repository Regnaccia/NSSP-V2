"""core layer: core_produzione_override (TASK-V2-030)

Revision ID: 20260407011
Revises: 20260407010
Create Date: 2026-04-08

Override interni per il Core slice `produzioni` (DL-ARCH-V2-015).
Tabella: core_produzione_override — PK (id_dettaglio, bucket).
Nessuna FK verso i mirror sync: indipendenza dei layer.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407011"
down_revision = "20260407010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_produzione_override",
        sa.Column("id_dettaglio", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(16), nullable=False),
        sa.Column("forza_completata", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id_dettaglio", "bucket"),
    )


def downgrade() -> None:
    op.drop_table("core_produzione_override")
