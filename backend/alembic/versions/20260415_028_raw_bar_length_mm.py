"""raw_bar_length_mm - add raw_bar_length_mm_enabled to articolo_famiglie and raw_bar_length_mm to core_articolo_config.

Revision ID: 20260415028
Revises: 20260414027
Create Date: 2026-04-15

Adds:
- articolo_famiglie.raw_bar_length_mm_enabled (BOOLEAN NOT NULL DEFAULT FALSE)
- core_articolo_config.raw_bar_length_mm (NUMERIC(10,4) NULL)

Il flag famiglia abilita la configurabilita del dato barra per gli articoli della famiglia.
Il campo articolo memorizza la lunghezza barra effettiva; non ha default famiglia.
(TASK-V2-118)
"""

from alembic import op
import sqlalchemy as sa

revision = "20260415028"
down_revision = "20260414027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articolo_famiglie",
        sa.Column(
            "raw_bar_length_mm_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "core_articolo_config",
        sa.Column("raw_bar_length_mm", sa.Numeric(10, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_articolo_config", "raw_bar_length_mm")
    op.drop_column("articolo_famiglie", "raw_bar_length_mm_enabled")
