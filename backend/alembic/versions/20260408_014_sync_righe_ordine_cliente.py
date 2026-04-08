"""sync_righe_ordine_cliente

Revision ID: 20260408014
Revises: 20260408013
Create Date: 2026-04-08

Crea la tabella sync_righe_ordine_cliente come mirror read-only di V_TORDCLI (EasyJob).
Source identity: (order_reference, line_reference) = (DOC_NUM, NUM_PROGR).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408014"
down_revision = "20260408013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_righe_ordine_cliente",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Source identity
        sa.Column("order_reference", sa.String(10), nullable=False),
        sa.Column("line_reference", sa.Integer(), nullable=False),
        # Dati testata ordine
        sa.Column("order_date", sa.DateTime(timezone=False), nullable=True),
        sa.Column("expected_delivery_date", sa.DateTime(timezone=False), nullable=True),
        # Riferimenti cliente e destinazione
        sa.Column("customer_code", sa.String(6), nullable=True),
        sa.Column("destination_code", sa.String(6), nullable=True),
        sa.Column("customer_destination_progressive", sa.String(6), nullable=True),
        sa.Column("customer_order_reference", sa.String(20), nullable=True),
        # Riferimenti articolo e descrizione
        sa.Column("article_code", sa.String(25), nullable=True),
        sa.Column("article_description_segment", sa.String(100), nullable=True),
        sa.Column("article_measure", sa.String(20), nullable=True),
        # Quantita
        sa.Column("ordered_qty", sa.Numeric(13, 5), nullable=True),
        sa.Column("fulfilled_qty", sa.Numeric(13, 5), nullable=True),
        sa.Column("set_aside_qty", sa.Numeric(18, 5), nullable=True),
        # Prezzo
        sa.Column("net_unit_price", sa.Numeric(18, 5), nullable=True),
        # Flag riga descrittiva
        sa.Column("continues_previous_line", sa.Boolean(), nullable=True),
        # Metadati sync
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        # Unique constraint su source identity
        sa.UniqueConstraint(
            "order_reference", "line_reference",
            name="uq_sync_righe_ordine_cliente_order_line",
        ),
    )


def downgrade() -> None:
    op.drop_table("sync_righe_ordine_cliente")
