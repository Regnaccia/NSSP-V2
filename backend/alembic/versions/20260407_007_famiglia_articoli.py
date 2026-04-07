"""Core: articolo_famiglie + core_articolo_config (TASK-V2-022)

Revision ID: 20260407007
Revises: 20260407006
Create Date: 2026-04-07

Catalogo famiglie articolo e configurazione interna per articolo.
Seed: materia_prima, articolo_standard, speciale, barre, conto_lavorazione.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407007"
down_revision = "20260407006"
branch_labels = None
depends_on = None

# ─── Seed famiglie (DL-ARCH-V2-014 §2) ───────────────────────────────────────

_FAMIGLIE_SEED = [
    {"code": "materia_prima",     "label": "Materia prima",     "sort_order": 1},
    {"code": "articolo_standard", "label": "Articolo standard", "sort_order": 2},
    {"code": "speciale",          "label": "Speciale",          "sort_order": 3},
    {"code": "barre",             "label": "Barre",             "sort_order": 4},
    {"code": "conto_lavorazione", "label": "Conto lavorazione", "sort_order": 5},
]


def upgrade() -> None:
    op.create_table(
        "articolo_famiglie",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "core_articolo_config",
        sa.Column("codice_articolo", sa.String(25), nullable=False),
        sa.Column("famiglia_code", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("codice_articolo"),
    )

    # Seed del catalogo famiglie
    famiglie_table = sa.table(
        "articolo_famiglie",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(famiglie_table, [
        {**f, "is_active": True} for f in _FAMIGLIE_SEED
    ])


def downgrade() -> None:
    op.drop_table("core_articolo_config")
    op.drop_table("articolo_famiglie")
