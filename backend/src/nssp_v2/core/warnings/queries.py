"""
Query Core slice `warnings` V1 (TASK-V2-076, TASK-V2-077, TASK-V2-081, TASK-V2-082, DL-ARCH-V2-029).

Regole:
- legge da core_availability (mai dai mirror sync direttamente)
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- genera warning NEGATIVE_STOCK per articoli con inventory_qty < 0
- il warning appartiene al modulo Warnings — nessun altro modulo lo possiede
- join cross-source con UPPER() per tollerare mismatch di casing (pattern TASK-V2-059)
- visible_to_areas e letto dalla config DB (TASK-V2-077, TASK-V2-081); default ['magazzino', 'produzione'] se non configurato

Filtro per area (TASK-V2-082):
- filter_warnings_by_areas: filtra la lista warning sulle aree utente derivate dai ruoli JWT
- admin vede tutti i warning indipendentemente da visible_to_areas
- ruoli operativi (produzione, magazzino, logistica) vedono solo i warning della propria area
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.warnings.config import get_visible_to_areas
from nssp_v2.core.warnings.logic import is_negative_stock
from nssp_v2.core.warnings.read_models import WarningItem
from nssp_v2.sync.articoli.models import SyncArticolo

_NEGATIVE_STOCK_TYPE = "NEGATIVE_STOCK"
_NEGATIVE_STOCK_SEVERITY = "warning"
_NEGATIVE_STOCK_ENTITY_TYPE = "article"
_NEGATIVE_STOCK_SOURCE = "warnings"


def list_warnings_v1(session: Session) -> list[WarningItem]:
    """Lista warning attivi V1.

    Genera WarningItem di tipo NEGATIVE_STOCK per ogni articolo attivo
    con inventory_qty < 0 in core_availability.

    visible_to_areas e risolto dalla config DB (TASK-V2-077, TASK-V2-081):
    se non esiste una riga per NEGATIVE_STOCK, usa il default ['magazzino', 'produzione'].

    Perimetro articoli: INNER JOIN su sync_articoli con attivo=True.
    Ordinamento: inventory_qty crescente (le anomalie piu gravi sopra).
    """
    areas = get_visible_to_areas(session, _NEGATIVE_STOCK_TYPE)

    rows = (
        session.query(CoreAvailability, SyncArticolo)
        .join(
            SyncArticolo,
            func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .filter(CoreAvailability.inventory_qty < 0)
        .order_by(CoreAvailability.inventory_qty)
        .all()
    )

    result: list[WarningItem] = []
    for avail, _art in rows:
        if not is_negative_stock(avail.inventory_qty):
            continue

        anomaly_qty = abs(avail.inventory_qty)
        result.append(WarningItem(
            warning_id=f"{_NEGATIVE_STOCK_TYPE}:{avail.article_code}",
            type=_NEGATIVE_STOCK_TYPE,
            severity=_NEGATIVE_STOCK_SEVERITY,
            entity_type=_NEGATIVE_STOCK_ENTITY_TYPE,
            entity_key=avail.article_code,
            message=(
                f"Giacenza fisica negativa per {avail.article_code}: "
                f"{avail.inventory_qty} (anomalia: {anomaly_qty})"
            ),
            source_module=_NEGATIVE_STOCK_SOURCE,
            visible_to_areas=areas,
            created_at=avail.computed_at,
            article_code=avail.article_code,
            stock_calculated=avail.inventory_qty,
            anomaly_qty=anomaly_qty,
        ))
    return result


def filter_warnings_by_areas(
    warnings: list[WarningItem],
    user_areas: list[str],
    is_admin: bool,
) -> list[WarningItem]:
    """Filtra i warning sulle aree operative dell'utente corrente (TASK-V2-082).

    Regole:
    - admin (is_admin=True): vede tutti i warning senza filtro
    - altri: vede solo i warning dove almeno una delle proprie aree e in visible_to_areas
    - se user_areas e vuota e non admin: nessun warning visibile

    user_areas deve contenere solo aree operative valide (produzione, magazzino, logistica).
    Derivate dai ruoli JWT escludendo 'admin' e altri ruoli non-area.
    """
    if is_admin:
        return list(warnings)
    return [
        w for w in warnings
        if any(area in w.visible_to_areas for area in user_areas)
    ]
