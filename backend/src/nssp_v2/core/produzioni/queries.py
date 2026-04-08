"""
Query del Core slice `produzioni` (DL-ARCH-V2-015).

Regole:
- legge da sync_produzioni_attive e sync_produzioni_storiche (mai modifica)
- legge e scrive core_produzione_override (solo per override interni: forza_completata)
- calcola stato_produzione come computed fact
- non espone dati sync grezzi alla UI
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from nssp_v2.core.produzioni.models import CoreProduzioneOverride
from nssp_v2.core.produzioni.read_models import ProduzioneItem, ProduzioniPaginata
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica


# ─── Helper: computed fact stato_produzione ──────────────────────────────────

def _compute_stato(
    quantita_ordinata: Decimal | None,
    quantita_prodotta: Decimal | None,
    forza_completata: bool,
) -> str:
    """Calcola stato_produzione (DL-ARCH-V2-015 §3-§5).

    Precedenza:
      1. forza_completata = True  ->  "completata"
      2. quantita_prodotta >= quantita_ordinata  ->  "completata"
      3. altrimenti  ->  "attiva"
    """
    if forza_completata:
        return "completata"
    if quantita_ordinata is not None and quantita_prodotta is not None:
        if quantita_prodotta >= quantita_ordinata:
            return "completata"
    return "attiva"


def _build_item(sync_obj, bucket: str, overrides: dict[tuple, "CoreProduzioneOverride"]) -> ProduzioneItem:
    key = (sync_obj.id_dettaglio, bucket)
    override = overrides.get(key)
    forza = override.forza_completata if override is not None else False
    return ProduzioneItem(
        id_dettaglio=sync_obj.id_dettaglio,
        bucket=bucket,
        cliente_ragione_sociale=sync_obj.cliente_ragione_sociale,
        codice_articolo=sync_obj.codice_articolo,
        descrizione_articolo=sync_obj.descrizione_articolo,
        numero_documento=sync_obj.numero_documento,
        numero_riga_documento=sync_obj.numero_riga_documento,
        quantita_ordinata=sync_obj.quantita_ordinata,
        quantita_prodotta=sync_obj.quantita_prodotta,
        stato_produzione=_compute_stato(
            sync_obj.quantita_ordinata,
            sync_obj.quantita_prodotta,
            forza,
        ),
        forza_completata=forza,
    )


# ─── Read model: lista produzioni paginata ───────────────────────────────────

_VALID_BUCKETS = {"active", "historical", "all"}
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


def list_produzioni(
    session: Session,
    bucket: str = "active",
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
) -> ProduzioniPaginata:
    """Restituisce le produzioni con filtro bucket e paginazione (TASK-V2-034).

    bucket:
      "active"     — solo sync_produzioni_attive (attivo=True)
      "historical" — solo sync_produzioni_storiche (attivo=True)
      "all"        — attive prima (per id_dettaglio), poi storiche (per id_dettaglio)

    Ordine stabile dentro ogni bucket: id_dettaglio ASC.
    Gli override forza_completata sono caricati filtrati per bucket corrente.

    Raises:
        ValueError: se bucket non e tra i valori ammessi.
    """
    if bucket not in _VALID_BUCKETS:
        raise ValueError(f"Bucket non valido: '{bucket}'. Valori ammessi: {sorted(_VALID_BUCKETS)}")

    limit = max(1, min(limit, _MAX_LIMIT))
    offset = max(0, offset)

    q_attive = (
        session.query(SyncProduzioneAttiva)
        .filter(SyncProduzioneAttiva.attivo == True)  # noqa: E712
        .order_by(SyncProduzioneAttiva.id_dettaglio)
    )
    q_storiche = (
        session.query(SyncProduzioneStorica)
        .filter(SyncProduzioneStorica.attivo == True)  # noqa: E712
        .order_by(SyncProduzioneStorica.id_dettaglio)
    )

    if bucket == "active":
        total = q_attive.count()
        rows_attive = q_attive.offset(offset).limit(limit).all()
        overrides = _load_overrides(session, "active", rows_attive)
        items = [_build_item(r, "active", overrides) for r in rows_attive]

    elif bucket == "historical":
        total = q_storiche.count()
        rows_storiche = q_storiche.offset(offset).limit(limit).all()
        overrides = _load_overrides_storica(session, rows_storiche)
        items = [_build_item(r, "historical", overrides) for r in rows_storiche]

    else:  # "all"
        count_a = q_attive.count()
        count_s = q_storiche.count()
        total = count_a + count_s

        items = []

        # Slice attive
        if offset < count_a:
            rows_a = q_attive.offset(offset).limit(limit).all()
            ov_a = _load_overrides(session, "active", rows_a)
            items.extend(_build_item(r, "active", ov_a) for r in rows_a)

        # Slice storiche (se servono ancora elementi)
        remaining = limit - len(items)
        if remaining > 0:
            storica_offset = max(0, offset - count_a)
            rows_s = q_storiche.offset(storica_offset).limit(remaining).all()
            ov_s = _load_overrides_storica(session, rows_s)
            items.extend(_build_item(r, "historical", ov_s) for r in rows_s)

    return ProduzioniPaginata(items=items, total=total, limit=limit, offset=offset)


def _load_overrides(
    session: Session,
    bucket: str,
    rows: list,
) -> dict[tuple, CoreProduzioneOverride]:
    """Carica gli override per un insieme di righe di un singolo bucket."""
    if not rows:
        return {}
    ids = [r.id_dettaglio for r in rows]
    return {
        (o.id_dettaglio, o.bucket): o
        for o in session.query(CoreProduzioneOverride)
        .filter(
            CoreProduzioneOverride.bucket == bucket,
            CoreProduzioneOverride.id_dettaglio.in_(ids),
        )
        .all()
    }


def _load_overrides_storica(
    session: Session,
    rows: list,
) -> dict[tuple, CoreProduzioneOverride]:
    return _load_overrides(session, "historical", rows)


# ─── Write: override forza_completata ────────────────────────────────────────

def set_forza_completata(
    session: Session,
    id_dettaglio: int,
    bucket: str,
    valore: bool,
) -> ProduzioneItem:
    """Imposta il flag forza_completata per una produzione.

    Crea il record di override se non esiste; aggiorna se esiste.
    Non modifica mai i mirror sync.

    Raises:
        ValueError: se il record non esiste in nessun mirror (id_dettaglio + bucket sconosciuti).
    """
    if bucket not in ("active", "historical"):
        raise ValueError(f"Bucket non valido: '{bucket}'. Valori ammessi: active, historical")

    # Verifica esistenza nel mirror corretto
    if bucket == "active":
        exists = (
            session.query(SyncProduzioneAttiva)
            .filter(
                SyncProduzioneAttiva.id_dettaglio == id_dettaglio,
                SyncProduzioneAttiva.attivo == True,  # noqa: E712
            )
            .first()
        )
        sync_obj = exists
    else:
        exists = (
            session.query(SyncProduzioneStorica)
            .filter(
                SyncProduzioneStorica.id_dettaglio == id_dettaglio,
                SyncProduzioneStorica.attivo == True,  # noqa: E712
            )
            .first()
        )
        sync_obj = exists

    if sync_obj is None:
        raise ValueError(
            f"Produzione id_dettaglio={id_dettaglio} bucket='{bucket}' non trovata"
        )

    # Upsert override
    override = session.get(CoreProduzioneOverride, (id_dettaglio, bucket))
    if override is None:
        override = CoreProduzioneOverride(
            id_dettaglio=id_dettaglio,
            bucket=bucket,
            forza_completata=valore,
        )
        session.add(override)
    else:
        override.forza_completata = valore
    session.flush()

    return _build_item(sync_obj, bucket, {(id_dettaglio, bucket): override})
