"""
Query del Core slice `availability` (TASK-V2-049, DL-ARCH-V2-021).

Regole:
- legge dai fact canonici del Core:
    - core_inventory_positions  (inventory_qty = on_hand_qty)
    - core_customer_set_aside   (aggregato per article_code)
    - core_commitments          (aggregato per article_code)
- mai dai mirror sync grezzi
- scrive solo su core_availability
- il rebuild e completo e deterministico: delete-all + re-insert
- availability_qty puo essere negativa (nessun clamp)
- i fact mancanti per articolo valgono 0

Rebuild:
  Step 1 — raccoglie tutti gli article_code attivi nei tre fact sorgente (union)
  Step 2 — per ogni articolo: aggrega inventory, set_aside e committed (default 0 se assente)
  Step 3 — delete-all + insert
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.availability.read_models import AvailabilityItem
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.shared.article_codes import normalize_article_code

_ZERO = Decimal("0")


# ─── Rebuild completo ─────────────────────────────────────────────────────────

def rebuild_availability(session: Session) -> int:
    """Ricostruisce completamente il fact availability dai tre fact canonici.

    Formula V1:
        availability_qty = inventory_qty - customer_set_aside_qty - committed_qty

    Strategia:
      1. raccoglie tutti gli article_code attivi (union dei tre fact sorgente)
      2. per ogni articolo: legge i contributi, usa 0 se il fact e assente
      3. elimina tutti i record esistenti
      4. inserisce i nuovi record

    Restituisce il numero di righe create.
    Non fa commit: il chiamante gestisce la transazione.
    """
    computed_at = datetime.now(timezone.utc)

    # Raccoglie inventory per article_code
    inventory_map: dict[str, Decimal] = {
        normalize_article_code(row.article_code): Decimal(str(row.on_hand_qty))
        for row in session.query(CoreInventoryPosition).all()
        if normalize_article_code(row.article_code) is not None
    }

    # Aggrega set_aside per article_code
    set_aside_map: dict[str, Decimal] = {}
    for row in (
        session.query(
            CoreCustomerSetAside.article_code,
            func.sum(CoreCustomerSetAside.set_aside_qty).label("total"),
        )
        .group_by(CoreCustomerSetAside.article_code)
        .all()
    ):
        article_code = normalize_article_code(row.article_code)
        if article_code is not None:
            set_aside_map[article_code] = Decimal(str(row.total))

    # Aggrega committed per article_code
    committed_map: dict[str, Decimal] = {}
    for row in (
        session.query(
            CoreCommitment.article_code,
            func.sum(CoreCommitment.committed_qty).label("total"),
        )
        .group_by(CoreCommitment.article_code)
        .all()
    ):
        article_code = normalize_article_code(row.article_code)
        if article_code is not None:
            committed_map[article_code] = Decimal(str(row.total))

    # Union degli article_code attivi nei tre fact
    all_codes: set[str] = (
        set(inventory_map) | set(set_aside_map) | set(committed_map)
    )

    new_records: list[CoreAvailability] = []
    for code in sorted(all_codes):
        inv = inventory_map.get(code, _ZERO)
        csa = set_aside_map.get(code, _ZERO)
        com = committed_map.get(code, _ZERO)
        new_records.append(CoreAvailability(
            article_code=code,
            inventory_qty=inv,
            customer_set_aside_qty=csa,
            committed_qty=com,
            availability_qty=inv - csa - com,
            computed_at=computed_at,
        ))

    session.query(CoreAvailability).delete(synchronize_session=False)
    session.flush()

    for r in new_records:
        session.add(r)
    session.flush()

    return len(new_records)


# ─── Read: lista disponibilita ────────────────────────────────────────────────

def list_availability(session: Session) -> list[AvailabilityItem]:
    """Restituisce tutte le posizioni di availability ordinate per article_code."""
    rows = (
        session.query(CoreAvailability)
        .order_by(CoreAvailability.article_code)
        .all()
    )
    return [_to_item(r) for r in rows]


def get_availability(session: Session, article_code: str) -> AvailabilityItem | None:
    """Restituisce la disponibilita di un singolo articolo, o None se assente."""
    normalized_article_code = normalize_article_code(article_code)
    if normalized_article_code is None:
        return None

    row = (
        session.query(CoreAvailability)
        .filter(CoreAvailability.article_code == normalized_article_code)
        .first()
    )
    return _to_item(row) if row is not None else None


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_item(row: CoreAvailability) -> AvailabilityItem:
    return AvailabilityItem(
        article_code=row.article_code,
        inventory_qty=row.inventory_qty,
        customer_set_aside_qty=row.customer_set_aside_qty,
        committed_qty=row.committed_qty,
        availability_qty=row.availability_qty,
        computed_at=row.computed_at,
    )
