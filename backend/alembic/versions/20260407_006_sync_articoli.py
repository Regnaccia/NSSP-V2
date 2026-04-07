"""sync layer: sync_articoli (TASK-V2-018)

Revision ID: 20260407006
Revises: 20260407005
Create Date: 2026-04-07

Mirror interno di ANAART (EasyJob).
Source identity: codice_articolo (ART_COD).
Dependencies: nessuna.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407006"
down_revision = "20260407005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_articoli",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_articolo", sa.String(25), nullable=False),
        sa.Column("descrizione_1", sa.String(100), nullable=True),
        sa.Column("descrizione_2", sa.String(100), nullable=True),
        sa.Column("unita_misura_codice", sa.String(3), nullable=True),
        sa.Column("source_modified_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("categoria_articolo_1", sa.String(6), nullable=True),
        sa.Column("materiale_grezzo_codice", sa.String(25), nullable=True),
        sa.Column("quantita_materiale_grezzo_occorrente", sa.Numeric(18, 5), nullable=True),
        sa.Column("quantita_materiale_grezzo_scarto", sa.Numeric(18, 5), nullable=True),
        sa.Column("misura_articolo", sa.String(20), nullable=True),
        sa.Column("codice_immagine", sa.String(3), nullable=True),
        sa.Column("contenitori_magazzino", sa.String(15), nullable=True),
        sa.Column("peso_grammi", sa.Numeric(18, 5), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codice_articolo"),
    )


def downgrade() -> None:
    op.drop_table("sync_articoli")
