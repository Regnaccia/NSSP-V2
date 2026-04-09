"""
Query del Core slice `customer_set_aside` (TASK-V2-044, DL-ARCH-V2-019).

Regole:
- legge dal Core ordini (customer_order_lines), mai da sync o Easy direttamente
- scrive solo su core_customer_set_aside
- il rebuild e completo e deterministico: delete-all + re-insert
- nessun calcolo di disponibilita in questo layer
- nessuna logica di modulo locale

Rebuild:
  Step 1 — legge list_customer_order_lines(session)
  Step 2 — filtra: article_code valorizzato e set_aside_qty > 0
  Step 3 — delete-all + insert

source_reference: "{order_reference}/{line_reference}"
source_type: "customer_order"
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.customer_set_aside.read_models import (
    CustomerSetAsideByArticleItem,
    CustomerSetAsideItem,
)
from nssp_v2.core.ordini_cliente.queries import list_customer_order_lines
from nssp_v2.shared.article_codes import normalize_article_code

_SOURCE_TYPE_CUSTOMER_ORDER = "customer_order"


# ─── Rebuild completo ─────────────────────────────────────────────────────────

def rebuild_customer_set_aside(session: Session) -> int:
    """Ricostruisce completamente il fact customer_set_aside da customer_order_lines.

    Logica V1:
      - set_aside_qty = DOC_QTAP dalla riga ordine canonica
      - solo righe con article_code valorizzato e set_aside_qty > 0
      - source_type = "customer_order"
      - source_reference = "{order_reference}/{line_reference}"

    Strategia:
      1. calcola i nuovi record dal Core ordini
      2. elimina tutti i record esistenti
      3. inserisce i nuovi record

    Restituisce il numero di righe create.
    Non fa commit: il chiamante gestisce la transazione.
    """
    computed_at = datetime.now(timezone.utc)

    order_lines = list_customer_order_lines(session)

    new_records: list[CoreCustomerSetAside] = []
    for line in order_lines:
        article_code = normalize_article_code(line.article_code)
        if article_code is None:
            continue
        qty = line.set_aside_qty
        if qty is None or qty <= Decimal("0"):
            continue
        new_records.append(CoreCustomerSetAside(
            article_code=article_code,
            source_type=_SOURCE_TYPE_CUSTOMER_ORDER,
            source_reference=f"{line.order_reference}/{line.line_reference}",
            set_aside_qty=qty,
            computed_at=computed_at,
        ))

    session.query(CoreCustomerSetAside).delete(synchronize_session=False)
    session.flush()

    for r in new_records:
        session.add(r)
    session.flush()

    return len(new_records)


# ─── Read: lista per riga ─────────────────────────────────────────────────────

def list_customer_set_aside(
    session: Session,
    source_type: str | None = None,
) -> list[CustomerSetAsideItem]:
    """Restituisce tutti i record attivi, opzionalmente filtrati per source_type.

    Args:
        session:     sessione SQLAlchemy
        source_type: se valorizzato, filtra per provenienza (es. "customer_order")
    """
    query = session.query(CoreCustomerSetAside).order_by(
        CoreCustomerSetAside.article_code,
        CoreCustomerSetAside.source_type,
        CoreCustomerSetAside.source_reference,
    )
    if source_type is not None:
        query = query.filter(CoreCustomerSetAside.source_type == source_type)

    return [_to_item(r) for r in query.all()]


# ─── Read: aggregazione per articolo ─────────────────────────────────────────

def get_customer_set_aside_by_article(
    session: Session,
    article_code: str | None = None,
) -> list[CustomerSetAsideByArticleItem]:
    """Restituisce il set aside aggregato per article_code.

    Args:
        session:      sessione SQLAlchemy
        article_code: se valorizzato, restituisce solo l'articolo specificato

    Restituisce lista vuota se non ci sono record attivi.
    """
    normalized_article_code = normalize_article_code(article_code)
    query = (
        session.query(
            CoreCustomerSetAside.article_code,
            func.sum(CoreCustomerSetAside.set_aside_qty).label("total_set_aside"),
            func.count(CoreCustomerSetAside.id).label("set_aside_count"),
            func.max(CoreCustomerSetAside.computed_at).label("computed_at"),
        )
        .group_by(CoreCustomerSetAside.article_code)
        .order_by(CoreCustomerSetAside.article_code)
    )
    if normalized_article_code is not None:
        query = query.filter(CoreCustomerSetAside.article_code == normalized_article_code)

    return [
        CustomerSetAsideByArticleItem(
            article_code=row.article_code,
            total_set_aside_qty=Decimal(str(row.total_set_aside)),
            set_aside_count=row.set_aside_count,
            computed_at=row.computed_at,
        )
        for row in query.all()
    ]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_item(row: CoreCustomerSetAside) -> CustomerSetAsideItem:
    return CustomerSetAsideItem(
        article_code=row.article_code,
        source_type=row.source_type,
        source_reference=row.source_reference,
        set_aside_qty=row.set_aside_qty,
        computed_at=row.computed_at,
    )
