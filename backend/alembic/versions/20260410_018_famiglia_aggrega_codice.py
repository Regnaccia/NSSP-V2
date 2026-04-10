"""famiglia_aggrega_codice

Revision ID: 20260410018
Revises: 20260409017
Create Date: 2026-04-10

Aggiunge il default di planning policy `aggrega_codice_in_produzione` alla tabella
`articolo_famiglie` (TASK-V2-063, DL-ARCH-V2-026).

Significato:
- se True, la famiglia indica che gli articoli sono aggregabili per codice nelle logiche
  operative di produzione/planning per default
- se False, gli articoli della famiglia non vengono aggregati automaticamente per codice
  senza logica piu specifica

Default False: comportamento conservativo — nessun articolo diventa aggregabile per codice
senza una scelta esplicita dell'utente.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260410018"
down_revision = "20260409017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articolo_famiglie",
        sa.Column(
            "aggrega_codice_in_produzione",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),  # compatibile con PostgreSQL e SQLite
        ),
    )


def downgrade() -> None:
    op.drop_column("articolo_famiglie", "aggrega_codice_in_produzione")
