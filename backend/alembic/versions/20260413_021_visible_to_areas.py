"""visible_to_areas — riallineamento vocabolario warning visibility (TASK-V2-081)

Revision ID: 20260413021
Revises: 20260413020
Create Date: 2026-04-13

Migrazione semantica: sostituisce il concetto di visibilita per singola surface
con visibilita per area/reparto operativo (TASK-V2-081, DL-ARCH-V2-029).

Operazioni:
1. Rinomina colonna `visible_in_surfaces` → `visible_to_areas`
2. Svuota le righe esistenti (semantic reset: i valori surface-based non sono
   mappabili ai nuovi valori area-based; il sistema usera i nuovi default)

Nuovi default per NEGATIVE_STOCK: ['magazzino', 'produzione']
Aree valide V1: magazzino, produzione, logistica
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413021"
down_revision = "20260413020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rinomina colonna (PostgreSQL supporta ALTER TABLE ... RENAME COLUMN)
    op.alter_column(
        "core_warning_type_config",
        "visible_in_surfaces",
        new_column_name="visible_to_areas",
    )
    # Reset semantico: i valori surface-based non sono mappabili alle aree
    op.execute("DELETE FROM core_warning_type_config")


def downgrade() -> None:
    op.alter_column(
        "core_warning_type_config",
        "visible_to_areas",
        new_column_name="visible_in_surfaces",
    )
