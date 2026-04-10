"""
Query Core slice `criticita articoli` (TASK-V2-055, DL-ARCH-V2-023, TASK-V2-056,
TASK-V2-057, TASK-V2-059, TASK-V2-060).

Regole:
- legge da core_availability (mai dai mirror sync direttamente)
- perimetro articoli (TASK-V2-060): solo codici presenti e attivi in sync_articoli —
  la vista criticita e un sottoinsieme operativo della surface articoli
- perimetro operativo default (TASK-V2-056): solo articoli la cui famiglia ha
  considera_in_produzione = True e is_active = True
- toggle solo_in_produzione (TASK-V2-057): se False, mostra tutti gli articoli critici
  nel perimetro articoli, indipendentemente dalla famiglia
- join cross-source con UPPER() per tollerare mismatch di casing tra chiave canonica
  (core_availability) e chiave raw (sync_articoli, core_articolo_config) (TASK-V2-059)
- arricchisce con sync_articoli (descrizione) e articolo_famiglie (label famiglia)
- applica la logica V1 tramite is_critical_v1 (DL-ARCH-V2-023 §Regola 3)
- la UI consuma CriticitaItem: nessuna formula hardcodata nel frontend
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.criticita.logic import ArticleLogicContext, is_critical_v1
from nssp_v2.core.criticita.read_models import CriticitaItem
from nssp_v2.sync.articoli.models import SyncArticolo


def _display_label(d1: str | None, d2: str | None, article_code: str) -> str:
    """Campo sintetico di presentazione (DL-ARCH-V2-013 §6)."""
    d1 = (d1 or "").strip()
    d2 = (d2 or "").strip()
    if d1 and d2:
        return f"{d1} {d2}"
    if d1:
        return d1
    return article_code


def list_criticita_v1(session: Session, *, solo_in_produzione: bool = True) -> list[CriticitaItem]:
    """Lista articoli critici V1 nel perimetro della surface articoli.

    Perimetro articoli (TASK-V2-060): INNER JOIN su sync_articoli con attivo=True.
    La vista criticita e un sottoinsieme operativo della surface articoli: un codice
    con availability_qty < 0 ma assente o non attivo in sync_articoli non appare.

    solo_in_produzione=True (default, TASK-V2-056):
        Solo articoli la cui famiglia ha considera_in_produzione = True e is_active = True.
        Articoli senza famiglia assegnata sono esclusi.

    solo_in_produzione=False (TASK-V2-057):
        Tutti gli articoli critici nel perimetro articoli, indipendentemente dalla famiglia.
        Utile per debug e popolamento dati durante la configurazione delle famiglie.

    JOIN cross-source (TASK-V2-059):
        Le join usano UPPER() sul lato raw per tollerare mismatch di casing tra la chiave
        canonica di core_availability e i codici conservati nei mirror.

    Logica (DL-ARCH-V2-023): is_critical_v1(ctx) — V1 = availability_qty < 0.
    Ordinamento default: availability_qty crescente (i peggiori sopra).
    """
    q = (
        session.query(CoreAvailability, SyncArticolo, CoreArticoloConfig, ArticoloFamiglia)
        .join(
            SyncArticolo,
            func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
        )
        .outerjoin(
            CoreArticoloConfig,
            func.upper(CoreArticoloConfig.codice_articolo) == CoreAvailability.article_code,
        )
        .outerjoin(
            ArticoloFamiglia,
            CoreArticoloConfig.famiglia_code == ArticoloFamiglia.code,
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .filter(CoreAvailability.availability_qty < 0)
    )

    if solo_in_produzione:
        q = q.filter(ArticoloFamiglia.considera_in_produzione == True)  # noqa: E712
        q = q.filter(ArticoloFamiglia.is_active == True)  # noqa: E712

    rows = q.order_by(CoreAvailability.availability_qty).all()

    result = []
    for avail, art, config, famiglia in rows:
        ctx = ArticleLogicContext(
            article_code=avail.article_code,
            inventory_qty=avail.inventory_qty,
            customer_set_aside_qty=avail.customer_set_aside_qty,
            committed_qty=avail.committed_qty,
            availability_qty=avail.availability_qty,
        )
        if not is_critical_v1(ctx):
            continue

        famiglia_code = famiglia.code if famiglia is not None else None
        famiglia_label = famiglia.label if famiglia is not None else None

        result.append(CriticitaItem(
            article_code=avail.article_code,
            descrizione_1=art.descrizione_1,
            descrizione_2=art.descrizione_2,
            display_label=_display_label(art.descrizione_1, art.descrizione_2, avail.article_code),
            famiglia_code=famiglia_code,
            famiglia_label=famiglia_label,
            inventory_qty=avail.inventory_qty,
            customer_set_aside_qty=avail.customer_set_aside_qty,
            committed_qty=avail.committed_qty,
            availability_qty=avail.availability_qty,
            computed_at=avail.computed_at,
        ))
    return result
