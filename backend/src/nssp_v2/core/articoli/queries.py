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
from sqlalchemy import func

from nssp_v2.core.articoli.read_models import ArticoloDetail, ArticoloItem, FamigliaItem, FamigliaRow
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition
from nssp_v2.shared.article_codes import normalize_article_code
from nssp_v2.sync.articoli.models import SyncArticolo


# ─── Helper: risoluzione planning policy effettiva ───────────────────────────

def resolve_planning_policy(
    override: bool | None,
    family_default: bool | None,
) -> bool | None:
    """Regola di risoluzione effective policy (DL-ARCH-V2-026 §4).

    effective = override if override is not None else family_default

    Restituisce:
    - override (True o False) se l'articolo ha un override esplicito
    - family_default se override e None e la famiglia e assegnata
    - None se override e None e non c'e famiglia (valore indefinito)

    I consumer devono consumare questo valore senza ricostruire la precedenza.
    """
    if override is not None:
        return override
    return family_default


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
        family_considera = famiglia.considera_in_produzione if famiglia else None
        family_aggrega = famiglia.aggrega_codice_in_produzione if famiglia else None
        override_considera = config.override_considera_in_produzione if config is not None else None
        override_aggrega = config.override_aggrega_codice_in_produzione if config is not None else None
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
            effective_considera_in_produzione=resolve_planning_policy(override_considera, family_considera),
            effective_aggrega_codice_in_produzione=resolve_planning_policy(override_aggrega, family_aggrega),
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
    family_considera = famiglia.considera_in_produzione if famiglia else None
    family_aggrega = famiglia.aggrega_codice_in_produzione if famiglia else None
    override_considera = config.override_considera_in_produzione if config is not None else None
    override_aggrega = config.override_aggrega_codice_in_produzione if config is not None else None
    normalized_article_code = normalize_article_code(art.codice_articolo)

    # Giacenza canonica (DL-ARCH-V2-016) — None se nessun movimento registrato
    inv = None
    if normalized_article_code is not None:
        inv = session.query(CoreInventoryPosition).filter(
            CoreInventoryPosition.article_code == normalized_article_code
        ).first()

    # Quota appartata per cliente (DL-ARCH-V2-019) — aggregata su tutte le righe ordine
    csa_row = (
        session.query(
            func.sum(CoreCustomerSetAside.set_aside_qty).label("total"),
            func.max(CoreCustomerSetAside.computed_at).label("computed_at"),
        )
        .filter(CoreCustomerSetAside.article_code == normalized_article_code)
        .first()
    )
    customer_set_aside_qty = csa_row.total if (csa_row and csa_row.total is not None) else None
    set_aside_computed_at = csa_row.computed_at if (csa_row and csa_row.total is not None) else None

    # Impegni totali per articolo (DL-ARCH-V2-017) — aggregati su tutte le provenienze
    com_row = (
        session.query(
            func.sum(CoreCommitment.committed_qty).label("total"),
            func.max(CoreCommitment.computed_at).label("computed_at"),
        )
        .filter(CoreCommitment.article_code == normalized_article_code)
        .first()
    )
    committed_qty = com_row.total if (com_row and com_row.total is not None) else None
    commitments_computed_at = com_row.computed_at if (com_row and com_row.total is not None) else None

    # Disponibilita canonica (DL-ARCH-V2-021)
    avail = session.query(CoreAvailability).filter(
        CoreAvailability.article_code == normalized_article_code
    ).first()

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
        effective_considera_in_produzione=resolve_planning_policy(override_considera, family_considera),
        effective_aggrega_codice_in_produzione=resolve_planning_policy(override_aggrega, family_aggrega),
        on_hand_qty=inv.on_hand_qty if inv is not None else None,
        giacenza_computed_at=inv.computed_at if inv is not None else None,
        customer_set_aside_qty=customer_set_aside_qty,
        set_aside_computed_at=set_aside_computed_at,
        committed_qty=committed_qty,
        commitments_computed_at=commitments_computed_at,
        availability_qty=avail.availability_qty if avail is not None else None,
        availability_computed_at=avail.computed_at if avail is not None else None,
    )


# ─── Read model: catalogo famiglie (gestione) ────────────────────────────────

def list_famiglie_catalog(session: Session) -> list[FamigliaRow]:
    """Restituisce tutte le famiglie (attive e inattive) con conteggio articoli assegnati.

    Usata dalla vista di gestione del catalogo famiglie.
    """
    counts: dict[str, int] = {
        code: n
        for code, n in session.query(
            CoreArticoloConfig.famiglia_code,
            func.count(CoreArticoloConfig.codice_articolo),
        )
        .filter(CoreArticoloConfig.famiglia_code.isnot(None))
        .group_by(CoreArticoloConfig.famiglia_code)
        .all()
    }

    rows = (
        session.query(ArticoloFamiglia)
        .order_by(ArticoloFamiglia.sort_order, ArticoloFamiglia.code)
        .all()
    )
    return [
        FamigliaRow(
            code=r.code,
            label=r.label,
            sort_order=r.sort_order,
            is_active=r.is_active,
            considera_in_produzione=r.considera_in_produzione,
            n_articoli=counts.get(r.code, 0),
        )
        for r in rows
    ]


# ─── Write: gestione catalogo famiglie ───────────────────────────────────────

def create_famiglia(
    session: Session,
    code: str,
    label: str,
    sort_order: int | None = None,
) -> FamigliaRow:
    """Crea una nuova famiglia articolo.

    Raises:
        ValueError: se code già esiste o label è vuota.
    """
    code = code.strip()
    label = label.strip()
    if not code:
        raise ValueError("Il codice famiglia non può essere vuoto")
    if not label:
        raise ValueError("La label famiglia non può essere vuota")

    existing = session.query(ArticoloFamiglia).filter(ArticoloFamiglia.code == code).first()
    if existing is not None:
        raise ValueError(f"Famiglia con code '{code}' già esistente")

    famiglia = ArticoloFamiglia(code=code, label=label, sort_order=sort_order, is_active=True)
    session.add(famiglia)
    session.flush()
    return FamigliaRow(
        code=famiglia.code,
        label=famiglia.label,
        sort_order=famiglia.sort_order,
        is_active=famiglia.is_active,
        considera_in_produzione=famiglia.considera_in_produzione,
        n_articoli=0,
    )


def toggle_famiglia_active(
    session: Session,
    code: str,
) -> FamigliaRow:
    """Inverte is_active della famiglia.

    Raises:
        ValueError: se la famiglia non esiste.
    """
    famiglia = session.query(ArticoloFamiglia).filter(ArticoloFamiglia.code == code).first()
    if famiglia is None:
        raise ValueError(f"Famiglia '{code}' non trovata")
    famiglia.is_active = not famiglia.is_active
    session.flush()
    n = session.query(CoreArticoloConfig).filter(CoreArticoloConfig.famiglia_code == code).count()
    return FamigliaRow(
        code=famiglia.code,
        label=famiglia.label,
        sort_order=famiglia.sort_order,
        is_active=famiglia.is_active,
        considera_in_produzione=famiglia.considera_in_produzione,
        n_articoli=n,
    )


def toggle_famiglia_considera_produzione(
    session: Session,
    code: str,
) -> FamigliaRow:
    """Inverte considera_in_produzione della famiglia.

    Raises:
        ValueError: se la famiglia non esiste.
    """
    famiglia = session.query(ArticoloFamiglia).filter(ArticoloFamiglia.code == code).first()
    if famiglia is None:
        raise ValueError(f"Famiglia '{code}' non trovata")
    famiglia.considera_in_produzione = not famiglia.considera_in_produzione
    session.flush()
    n = session.query(CoreArticoloConfig).filter(CoreArticoloConfig.famiglia_code == code).count()
    return FamigliaRow(
        code=famiglia.code,
        label=famiglia.label,
        sort_order=famiglia.sort_order,
        is_active=famiglia.is_active,
        considera_in_produzione=famiglia.considera_in_produzione,
        n_articoli=n,
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

    Raises:
        ValueError: se famiglia_code non esiste o è inattiva.
    """
    if famiglia_code is not None:
        famiglia = session.query(ArticoloFamiglia).filter(
            ArticoloFamiglia.code == famiglia_code
        ).first()
        if famiglia is None:
            raise ValueError(f"Famiglia '{famiglia_code}' non trovata")
        if not famiglia.is_active:
            raise ValueError(f"Famiglia '{famiglia_code}' non è attiva")

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
