"""
Query del Core slice `articoli` (DL-ARCH-V2-013, DL-ARCH-V2-014).

Regole:
- legge da sync_articoli (mai modifica)
- legge e scrive core_articolo_config (solo per dati interni: famiglia)
- legge articolo_famiglie (catalogo controllato)
- costruisce i read model applicativi
- non espone dati sync_articoli grezzi alla UI
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.read_models import ArticoloDetail, ArticoloItem, FamigliaItem
from nssp_v2.sync.articoli.models import SyncArticolo


# ─── Helper display_label ─────────────────────────────────────────────────────

def _compute_display_label(
    descrizione_1: str | None,
    descrizione_2: str | None,
    codice_articolo: str,
) -> str:
    """Campo sintetico di presentazione per un articolo (DL-ARCH-V2-013 §6).

    Ordine di precedenza:
      1. descrizione_1 + " " + descrizione_2 (se entrambe presenti e non vuote)
      2. descrizione_1 (se presente e non vuota)
      3. codice_articolo (fallback tecnico)
    """
    d1 = (descrizione_1 or "").strip()
    d2 = (descrizione_2 or "").strip()

    if d1 and d2:
        return f"{d1} {d2}"
    if d1:
        return d1
    return codice_articolo


# ─── Helper: carica mappa famiglie ───────────────────────────────────────────

def _load_famiglie_map(session: Session) -> dict[str, ArticoloFamiglia]:
    """Carica il catalogo famiglie come mappa code -> oggetto."""
    return {
        f.code: f
        for f in session.query(ArticoloFamiglia).filter(ArticoloFamiglia.is_active == True).all()  # noqa: E712
    }


# ─── Read model: catalogo famiglie ───────────────────────────────────────────

def list_famiglie(session: Session) -> list[FamigliaItem]:
    """Restituisce il catalogo famiglie articolo attive, ordinate per sort_order."""
    rows = (
        session.query(ArticoloFamiglia)
        .filter(ArticoloFamiglia.is_active == True)  # noqa: E712
        .order_by(ArticoloFamiglia.sort_order, ArticoloFamiglia.code)
        .all()
    )
    return [
        FamigliaItem(code=r.code, label=r.label, sort_order=r.sort_order)
        for r in rows
    ]


# ─── Read model: lista articoli ──────────────────────────────────────────────

def list_articoli(session: Session) -> list[ArticoloItem]:
    """Restituisce la lista articoli attivi con famiglia interna, ordinata per codice.

    Sorgente: sync_articoli (attivo=True) + core_articolo_config (LEFT JOIN) + articolo_famiglie.
    """
    famiglie = _load_famiglie_map(session)

    rows = (
        session.query(SyncArticolo, CoreArticoloConfig)
        .outerjoin(
            CoreArticoloConfig,
            SyncArticolo.codice_articolo == CoreArticoloConfig.codice_articolo,
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .order_by(SyncArticolo.codice_articolo)
        .all()
    )

    result = []
    for art, config in rows:
        famiglia_code = config.famiglia_code if config is not None else None
        famiglia = famiglie.get(famiglia_code) if famiglia_code else None
        result.append(ArticoloItem(
            codice_articolo=art.codice_articolo,
            descrizione_1=art.descrizione_1,
            descrizione_2=art.descrizione_2,
            unita_misura_codice=art.unita_misura_codice,
            display_label=_compute_display_label(
                art.descrizione_1, art.descrizione_2, art.codice_articolo
            ),
            famiglia_code=famiglia_code,
            famiglia_label=famiglia.label if famiglia else None,
        ))
    return result


# ─── Read model: dettaglio articolo ──────────────────────────────────────────

def get_articolo_detail(
    session: Session,
    codice_articolo: str,
) -> ArticoloDetail | None:
    """Restituisce il dettaglio completo di un articolo con famiglia interna.

    Restituisce None se l'articolo non esiste in sync_articoli.
    """
    famiglie = _load_famiglie_map(session)

    row = (
        session.query(SyncArticolo, CoreArticoloConfig)
        .outerjoin(
            CoreArticoloConfig,
            SyncArticolo.codice_articolo == CoreArticoloConfig.codice_articolo,
        )
        .filter(SyncArticolo.codice_articolo == codice_articolo)
        .first()
    )
    if row is None:
        return None

    art, config = row
    famiglia_code = config.famiglia_code if config is not None else None
    famiglia = famiglie.get(famiglia_code) if famiglia_code else None

    return ArticoloDetail(
        codice_articolo=art.codice_articolo,
        descrizione_1=art.descrizione_1,
        descrizione_2=art.descrizione_2,
        unita_misura_codice=art.unita_misura_codice,
        source_modified_at=art.source_modified_at,
        categoria_articolo_1=art.categoria_articolo_1,
        materiale_grezzo_codice=art.materiale_grezzo_codice,
        quantita_materiale_grezzo_occorrente=art.quantita_materiale_grezzo_occorrente,
        quantita_materiale_grezzo_scarto=art.quantita_materiale_grezzo_scarto,
        misura_articolo=art.misura_articolo,
        codice_immagine=art.codice_immagine,
        contenitori_magazzino=art.contenitori_magazzino,
        peso_grammi=art.peso_grammi,
        display_label=_compute_display_label(
            art.descrizione_1, art.descrizione_2, art.codice_articolo
        ),
        famiglia_code=famiglia_code,
        famiglia_label=famiglia.label if famiglia else None,
    )


# ─── Write: imposta famiglia articolo ────────────────────────────────────────

def set_famiglia_articolo(
    session: Session,
    codice_articolo: str,
    famiglia_code: str | None,
) -> None:
    """Imposta o rimuove la famiglia interna di un articolo.

    Non modifica mai sync_articoli.
    famiglia_code=None rimuove l'associazione.
    """
    config = session.get(CoreArticoloConfig, codice_articolo)
    now = datetime.now(timezone.utc)

    if config is None:
        config = CoreArticoloConfig(
            codice_articolo=codice_articolo,
            famiglia_code=famiglia_code,
            updated_at=now,
        )
        session.add(config)
    else:
        config.famiglia_code = famiglia_code
        config.updated_at = now

    session.flush()
