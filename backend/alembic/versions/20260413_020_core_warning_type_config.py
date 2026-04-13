"""core_warning_type_config

Revision ID: 20260413020
Revises: 20260410019
Create Date: 2026-04-13

Crea la tabella `core_warning_type_config` per la configurazione di visibilita
dei warning del modulo Warnings (TASK-V2-077, DL-ARCH-V2-029).

Schema:
- warning_type: tipo warning canonico (es. NEGATIVE_STOCK)
- visible_in_surfaces: JSON list di codici surface (es. ['articoli', 'warnings'])
- updated_at: timestamp ultimo aggiornamento

Un record per tipo warning. Se non esiste, si usa il default del tipo.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413020"
down_revision = "20260410019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_warning_type_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("warning_type", sa.String(64), nullable=False),
        sa.Column("visible_in_surfaces", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("warning_type", name="uq_core_warning_type_config_type"),
    )


def downgrade() -> None:
    op.drop_table("core_warning_type_config")
