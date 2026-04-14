"""stock_logic_config — configurazione logiche stock V1 (TASK-V2-086, DL-ARCH-V2-030)

Revision ID: 20260413023
Revises: 20260413022
Create Date: 2026-04-13

Crea la tabella `core_stock_logic_config` per la configurazione interna V2 delle
logiche di calcolo delle metriche stock V1.

Schema (singleton: al massimo un record con id=1):
- monthly_base_strategy_key: strategy selezionata per monthly_stock_base_qty
- monthly_base_params_json: parametri JSON della strategy selezionata
- capacity_logic_key: logica capacity (fisso: 'capacity_from_containers_v1')
- capacity_logic_params_json: parametri JSON della logica capacity
- updated_at: timestamp aggiornamento

Se la tabella e vuota, il Core usa i valori di default definiti nel codice.
La strategy_key deve appartenere al registry chiuso KNOWN_MONTHLY_BASE_STRATEGIES.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413023"
down_revision = "20260413022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_stock_logic_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("monthly_base_strategy_key", sa.String(64), nullable=False),
        sa.Column("monthly_base_params_json", sa.JSON(), nullable=False),
        sa.Column("capacity_logic_key", sa.String(64), nullable=False),
        sa.Column("capacity_logic_params_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("core_stock_logic_config")
