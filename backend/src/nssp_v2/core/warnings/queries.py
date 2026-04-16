"""
Query Core slice `warnings` V1 (TASK-V2-076, TASK-V2-077, TASK-V2-081, TASK-V2-082, DL-ARCH-V2-029, TASK-V2-091).

Regole:
- legge da core_availability (mai dai mirror sync direttamente)
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- genera warning NEGATIVE_STOCK per articoli con inventory_qty < 0
- genera warning INVALID_STOCK_CAPACITY per articoli by_article con capacity_effective_qty None o <= 0
- il warning appartiene al modulo Warnings — nessun altro modulo lo possiede
- join cross-source con UPPER() per tollerare mismatch di casing (pattern TASK-V2-059)
- visible_to_areas e letto dalla config DB (TASK-V2-077, TASK-V2-081); default dal tipo se non configurato

Filtro per area (TASK-V2-082):
- filter_warnings_by_areas: filtra la lista warning sulle aree utente derivate dai ruoli JWT
- admin vede tutti i warning indipendentemente da visible_to_areas
- ruoli operativi (produzione, magazzino, logistica) vedono solo i warning della propria area
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.warnings.config import get_visible_to_areas
from nssp_v2.core.warnings.logic import is_invalid_stock_capacity, is_missing_raw_bar_length, is_negative_stock
from nssp_v2.core.warnings.read_models import WarningItem
from nssp_v2.sync.articoli.models import SyncArticolo

_NEGATIVE_STOCK_TYPE = "NEGATIVE_STOCK"
_INVALID_STOCK_CAPACITY_TYPE = "INVALID_STOCK_CAPACITY"
_MISSING_RAW_BAR_LENGTH_TYPE = "MISSING_RAW_BAR_LENGTH"
_WARNING_SEVERITY = "warning"
_ENTITY_TYPE_ARTICLE = "article"
_SOURCE_MODULE = "warnings"


def list_warnings_v1(session: Session) -> list[WarningItem]:
    """Lista warning attivi V1.

    Genera:
    - NEGATIVE_STOCK: articoli attivi con inventory_qty < 0
    - INVALID_STOCK_CAPACITY: articoli attivi by_article con capacity_effective_qty None o <= 0
    - MISSING_RAW_BAR_LENGTH: articoli in famiglia con raw_bar_length_mm_enabled=True
      ma raw_bar_length_mm assente o <= 0

    visible_to_areas e risolto dalla config DB; default dal tipo se non configurato.
    Perimetro articoli: INNER JOIN su sync_articoli con attivo=True.
    Ordinamento NEGATIVE_STOCK: inventory_qty crescente (anomalie piu gravi sopra).
    Ordinamento INVALID_STOCK_CAPACITY: article_code alfabetico.
    Ordinamento MISSING_RAW_BAR_LENGTH: article_code alfabetico.
    """
    result: list[WarningItem] = []

    # ─── NEGATIVE_STOCK ───────────────────────────────────────────────────────
    areas_neg = get_visible_to_areas(session, _NEGATIVE_STOCK_TYPE)

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

    for avail, _art in rows:
        if not is_negative_stock(avail.inventory_qty):
            continue
        anomaly_qty = abs(avail.inventory_qty)
        result.append(WarningItem(
            warning_id=f"{_NEGATIVE_STOCK_TYPE}:{avail.article_code}",
            type=_NEGATIVE_STOCK_TYPE,
            severity=_WARNING_SEVERITY,
            entity_type=_ENTITY_TYPE_ARTICLE,
            entity_key=avail.article_code,
            message=(
                f"Giacenza fisica negativa per {avail.article_code}: "
                f"{avail.inventory_qty} (anomalia: {anomaly_qty})"
            ),
            source_module=_SOURCE_MODULE,
            visible_to_areas=areas_neg,
            created_at=avail.computed_at,
            article_code=avail.article_code,
            stock_calculated=avail.inventory_qty,
            anomaly_qty=anomaly_qty,
        ))

    # ─── INVALID_STOCK_CAPACITY (TASK-V2-091) ─────────────────────────────────
    # Import lazy per evitare circular import (stock_policy -> articoli.models -> articoli.__init__)
    from nssp_v2.core.stock_policy import list_stock_metrics_v1  # noqa: PLC0415

    areas_cap = get_visible_to_areas(session, _INVALID_STOCK_CAPACITY_TYPE)
    metrics = list_stock_metrics_v1(session)

    for m in sorted(metrics, key=lambda x: x.article_code):
        if not is_invalid_stock_capacity(m.capacity_effective_qty):
            continue
        result.append(WarningItem(
            warning_id=f"{_INVALID_STOCK_CAPACITY_TYPE}:{m.article_code}",
            type=_INVALID_STOCK_CAPACITY_TYPE,
            severity=_WARNING_SEVERITY,
            entity_type=_ENTITY_TYPE_ARTICLE,
            entity_key=m.article_code,
            message=(
                f"Capacity non configurata per {m.article_code} "
                f"(calcolata: {m.capacity_calculated_qty}, override: {m.capacity_override_qty})"
            ),
            source_module=_SOURCE_MODULE,
            visible_to_areas=areas_cap,
            created_at=m.computed_at,
            article_code=m.article_code,
            capacity_calculated_qty=m.capacity_calculated_qty,
            capacity_override_qty=m.capacity_override_qty,
            capacity_effective_qty=m.capacity_effective_qty,
        ))

    # ─── MISSING_RAW_BAR_LENGTH (TASK-V2-126) ─────────────────────────────────
    # Logica riallineata: raw_bar_length_mm e sul materiale grezzo, non sul finito.
    # Per ogni finito in famiglia con raw_bar_length_mm_enabled=True:
    #   1. Risolve materiale_grezzo_codice da SyncArticolo del finito.
    #   2. Controlla raw_bar_length_mm su CoreArticoloConfig del materiale grezzo.
    #   3. Se mancante/invalido, genera warning sull'articolo materiale grezzo (deduplicato).
    areas_bar = get_visible_to_areas(session, _MISSING_RAW_BAR_LENGTH_TYPE)

    bar_rows = (
        session.query(CoreArticoloConfig, ArticoloFamiglia, SyncArticolo)
        .join(ArticoloFamiglia, CoreArticoloConfig.famiglia_code == ArticoloFamiglia.code)
        .join(
            SyncArticolo,
            func.upper(SyncArticolo.codice_articolo) == func.upper(CoreArticoloConfig.codice_articolo),
        )
        .filter(ArticoloFamiglia.raw_bar_length_mm_enabled == True)  # noqa: E712
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .all()
    )

    seen_raw_material_keys: set[str] = set()
    for _cfg, famiglia, art in sorted(bar_rows, key=lambda r: r[0].codice_articolo.strip().upper()):
        raw_mat_code = (art.materiale_grezzo_codice or "").strip()
        if not raw_mat_code:
            continue  # nessun materiale grezzo → nessun controllo barra
        raw_mat_key = raw_mat_code.upper()
        if raw_mat_key in seen_raw_material_keys:
            continue
        seen_raw_material_keys.add(raw_mat_key)

        raw_mat_cfg = session.scalar(
            select(CoreArticoloConfig).where(
                func.upper(CoreArticoloConfig.codice_articolo) == raw_mat_key
            )
        )
        raw_bar_length_mm_val = raw_mat_cfg.raw_bar_length_mm if raw_mat_cfg is not None else None
        if not is_missing_raw_bar_length(raw_bar_length_mm_val):
            continue

        raw_mat_art = session.scalar(
            select(SyncArticolo).where(
                func.upper(SyncArticolo.codice_articolo) == raw_mat_key
            )
        )
        created_at_val = raw_mat_art.synced_at if raw_mat_art else art.synced_at

        result.append(WarningItem(
            warning_id=f"{_MISSING_RAW_BAR_LENGTH_TYPE}:{raw_mat_key}",
            type=_MISSING_RAW_BAR_LENGTH_TYPE,
            severity=_WARNING_SEVERITY,
            entity_type=_ENTITY_TYPE_ARTICLE,
            entity_key=raw_mat_key,
            message=(
                f"Lunghezza barra grezza mancante o non valida per materiale {raw_mat_key} "
                f"(famiglia finito {famiglia.code} ha raw_bar_length_mm_enabled=True)"
            ),
            source_module=_SOURCE_MODULE,
            visible_to_areas=areas_bar,
            created_at=created_at_val,
            article_code=raw_mat_key,
            famiglia_code=famiglia.code,
            raw_bar_length_mm_enabled=True,
            raw_bar_length_mm=raw_bar_length_mm_val,
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
