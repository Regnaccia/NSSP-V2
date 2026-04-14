"""gestione_scorte_attiva — flag esplicito stock policy su famiglia e articolo (TASK-V2-096)

Revision ID: 20260413024
Revises: 20260413023
Create Date: 2026-04-13

Aggiunge:
- articolo_famiglie.gestione_scorte_attiva (Boolean, NOT NULL, default False)
  Flag esplicito di applicabilita della stock policy per la famiglia.
  False = stock policy non attiva (default conservativo).
  True  = stock policy attiva (prerequisito: planning_mode = by_article).

- core_articolo_config.override_gestione_scorte_attiva (Boolean, nullable)
  Override tri-state articolo-specifico: None = eredita dalla famiglia.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413024"
down_revision = "20260413023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articolo_famiglie",
        sa.Column(
            "gestione_scorte_attiva",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "core_articolo_config",
        sa.Column("override_gestione_scorte_attiva", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_articolo_config", "override_gestione_scorte_attiva")
    op.drop_column("articolo_famiglie", "gestione_scorte_attiva")
