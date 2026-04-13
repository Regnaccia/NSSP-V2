"""stock_policy_config — configurazione stock policy V1 (TASK-V2-083, DL-ARCH-V2-030)

Revision ID: 20260413022
Revises: 20260413021
Create Date: 2026-04-13

Aggiunge il modello configurativo minimo della stock policy V1:

Tabella articolo_famiglie (default famiglia):
- stock_months: mesi di scorta target (nullable — None = nessun default)
- stock_trigger_months: mesi di soglia trigger (nullable)

Tabella core_articolo_config (override articolo):
- override_stock_months: override puntuale per stock_months (nullable)
- override_stock_trigger_months: override puntuale per stock_trigger_months (nullable)
- capacity_override_qty: capacita produttiva override (nullable — nessun default famiglia)

La logica di risoluzione effettiva segue la stessa regola gia adottata per la planning policy:
    effective = override if override is not None else family_default
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413022"
down_revision = "20260413021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Default stock policy sulla famiglia
    op.add_column("articolo_famiglie", sa.Column("stock_months", sa.Numeric(10, 4), nullable=True))
    op.add_column("articolo_famiglie", sa.Column("stock_trigger_months", sa.Numeric(10, 4), nullable=True))

    # Override stock policy e capacity sull'articolo
    op.add_column("core_articolo_config", sa.Column("override_stock_months", sa.Numeric(10, 4), nullable=True))
    op.add_column("core_articolo_config", sa.Column("override_stock_trigger_months", sa.Numeric(10, 4), nullable=True))
    op.add_column("core_articolo_config", sa.Column("capacity_override_qty", sa.Numeric(14, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("core_articolo_config", "capacity_override_qty")
    op.drop_column("core_articolo_config", "override_stock_trigger_months")
    op.drop_column("core_articolo_config", "override_stock_months")
    op.drop_column("articolo_famiglie", "stock_trigger_months")
    op.drop_column("articolo_famiglie", "stock_months")
