"""sync_clienti: aggiungi campi da EASY_CLIENTI.md (TASK-V2-010)

Revision ID: 20260407003
Revises: 20260407002
Create Date: 2026-04-07

Aggiunge le colonne necessarie per allineare sync_clienti al mapping
documentato in EASY_CLIENTI.md:
  indirizzo          <- CLI_IND   (nullable)
  nazione_codice     <- NAZ_COD   (nullable)
  provincia          <- PROV      (nullable)
  telefono_1         <- CLI_TEL1  (nullable)
  source_modified_at <- CLI_DTMO  (nullable, no timezone — datetime SQL Server)
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407003"
down_revision = "20260407002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sync_clienti", sa.Column("indirizzo", sa.String(255), nullable=True))
    op.add_column("sync_clienti", sa.Column("nazione_codice", sa.String(16), nullable=True))
    op.add_column("sync_clienti", sa.Column("provincia", sa.String(4), nullable=True))
    op.add_column("sync_clienti", sa.Column("telefono_1", sa.String(64), nullable=True))
    op.add_column("sync_clienti", sa.Column("source_modified_at", sa.DateTime(timezone=False), nullable=True))


def downgrade() -> None:
    op.drop_column("sync_clienti", "source_modified_at")
    op.drop_column("sync_clienti", "telefono_1")
    op.drop_column("sync_clienti", "provincia")
    op.drop_column("sync_clienti", "nazione_codice")
    op.drop_column("sync_clienti", "indirizzo")
