"""sync layer: sync_produzioni_attive (TASK-V2-028)

Revision ID: 20260407009
Revises: 20260407008
Create Date: 2026-04-08

Mirror interno di DPRE_PROD (EasyJob).
Source identity: id_dettaglio (ID_DETTAGLIO).
Dependencies: nessuna.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407009"
down_revision = "20260407008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_produzioni_attive",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_dettaglio", sa.Integer(), nullable=False),
        sa.Column("cliente_ragione_sociale", sa.String(55), nullable=True),
        sa.Column("codice_articolo", sa.String(25), nullable=True),
        sa.Column("descrizione_articolo", sa.String(100), nullable=True),
        sa.Column("descrizione_articolo_2", sa.String(150), nullable=True),
        sa.Column("numero_riga_documento", sa.Integer(), nullable=True),
        sa.Column("quantita_ordinata", sa.Numeric(18, 5), nullable=True),
        sa.Column("quantita_prodotta", sa.Numeric(18, 5), nullable=True),
        sa.Column("materiale_partenza_codice", sa.String(25), nullable=True),
        sa.Column("materiale_partenza_per_pezzo", sa.Numeric(18, 5), nullable=True),
        sa.Column("misura_articolo", sa.String(20), nullable=True),
        sa.Column("numero_documento", sa.String(10), nullable=True),
        sa.Column("codice_immagine", sa.String(1), nullable=True),
        sa.Column("riferimento_numero_ordine_cliente", sa.String(10), nullable=True),
        sa.Column("riferimento_riga_ordine_cliente", sa.Numeric(18, 0), nullable=True),
        sa.Column("note_articolo", sa.String(55), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_dettaglio"),
    )


def downgrade() -> None:
    op.drop_table("sync_produzioni_attive")
