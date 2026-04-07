"""Core layer: core_destinazione_config (TASK-V2-012)

Revision ID: 20260407005
Revises: 20260407004
Create Date: 2026-04-07

Primo dato interno configurabile del Core slice clienti + destinazioni.
Keyed su codice_destinazione (stessa source identity del layer sync).
Nessuna FK hard verso sync_destinazioni (decoupling intenzionale).

Campi:
- codice_destinazione: PK, identita tecnica della destinazione
- nickname_destinazione: nome leggibile interno, nullable
- updated_at: timestamp ultimo aggiornamento
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407005"
down_revision = "20260407004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_destinazione_config",
        sa.Column("codice_destinazione", sa.String(32), nullable=False),
        sa.Column("nickname_destinazione", sa.String(128), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("codice_destinazione"),
    )


def downgrade() -> None:
    op.drop_table("core_destinazione_config")
