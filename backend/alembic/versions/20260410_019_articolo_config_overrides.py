"""articolo_config_overrides

Revision ID: 20260410019
Revises: 20260410018
Create Date: 2026-04-10

Aggiunge override nullable tri-state a `core_articolo_config` per le planning policy
(TASK-V2-063, DL-ARCH-V2-026):

- `override_considera_in_produzione` (Boolean nullable):
    null  = eredita dalla famiglia (comportamento attuale)
    True  = includi nell'operativo di planning/produzione, indipendentemente dalla famiglia
    False = escludi dall'operativo di planning/produzione, indipendentemente dalla famiglia

- `override_aggrega_codice_in_produzione` (Boolean nullable):
    null  = eredita dalla famiglia
    True  = aggregabile per codice, indipendentemente dalla famiglia
    False = non aggregabile per codice, indipendentemente dalla famiglia

Regola di risoluzione (DL-ARCH-V2-026 §Effective policy):
    effective_value = override if override is not None else family_default
"""

from alembic import op
import sqlalchemy as sa

revision = "20260410019"
down_revision = "20260410018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_articolo_config",
        sa.Column(
            "override_considera_in_produzione",
            sa.Boolean(),
            nullable=True,
        ),
    )
    op.add_column(
        "core_articolo_config",
        sa.Column(
            "override_aggrega_codice_in_produzione",
            sa.Boolean(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("core_articolo_config", "override_aggrega_codice_in_produzione")
    op.drop_column("core_articolo_config", "override_considera_in_produzione")
