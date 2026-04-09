"""
Query del Core slice `commitments` (TASK-V2-042, TASK-V2-043, DL-ARCH-V2-017).

Regole:
- legge dal Core ordini (customer_order_lines) per la provenienza customer_order
- legge da sync_produzioni_attive + Core produzioni per la provenienza production
  (applica la stessa logica di stato "attiva" del Core produzioni)
- scrive solo su core_commitments
- il rebuild e completo e deterministico: delete-all + re-insert
- nessun calcolo di disponibilita in questo layer
- nessuna logica di modulo locale

Rebuild:
  Step 1 — customer_order:
    list_customer_order_lines(session) -> filtra open_qty > 0 e article_code valorizzato
    committed_qty = open_qty

  Step 2 — production:
    sync_produzioni_attive (attivo=True, stato="attiva")
    join sync_articoli su materiale_partenza_codice per CAT_ART1 lookup
    filtra CAT_ART1 != "0" (esclude materia prima in mm)
    committed_qty = materiale_partenza_per_pezzo (MM_PEZZO)

source_reference:
  customer_order: "{order_reference}/{line_reference}"
  production:     "{id_dettaglio}"
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.core.commitments.read_models import CommitmentItem, CommitmentsByArticleItem
from nssp_v2.core.ordini_cliente.queries import list_customer_order_lines
from nssp_v2.core.produzioni.models import CoreProduzioneOverride
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva

_SOURCE_TYPE_CUSTOMER_ORDER = "customer_order"
_SOURCE_TYPE_PRODUCTION = "production"


# ─── Rebuild completo ─────────────────────────────────────────────────────────

def rebuild_commitments(session: Session) -> int:
    """Ricostruisce completamente i commitments da tutte le provenienze attive.

    Provenienze V1:
      - customer_order: open_qty da customer_order_lines (Core ordini)
      - production:     MM_PEZZO da produzioni attive non completate (Core produzioni)

    Strategia comune:
      1. calcola i nuovi commitments da ogni provenienza
      2. elimina tutti i commitments esistenti
      3. inserisce i nuovi commitments

    Restituisce il numero totale di righe di commitment create.
    Non fa commit: il chiamante gestisce la transazione.
    """
    computed_at = datetime.now(timezone.utc)

    new_commitments: list[CoreCommitment] = []

    # ── Provenienza 1: customer_order ─────────────────────────────────────────
    order_lines = list_customer_order_lines(session)
    for line in order_lines:
        if line.article_code is not None and line.open_qty > Decimal("0"):
            new_commitments.append(CoreCommitment(
                article_code=line.article_code,
                source_type=_SOURCE_TYPE_CUSTOMER_ORDER,
                source_reference=f"{line.order_reference}/{line.line_reference}",
                committed_qty=line.open_qty,
                computed_at=computed_at,
            ))

    # ── Provenienza 2: production ─────────────────────────────────────────────
    production_commitments = _build_production_commitments(session, computed_at)
    new_commitments.extend(production_commitments)

    # ── Delete all e re-insert ────────────────────────────────────────────────
    session.query(CoreCommitment).delete(synchronize_session=False)
    session.flush()

    for c in new_commitments:
        session.add(c)
    session.flush()

    return len(new_commitments)


# ─── Helper: provenienza production ──────────────────────────────────────────

def _build_production_commitments(
    session: Session,
    computed_at: datetime,
) -> list[CoreCommitment]:
    """Costruisce i CoreCommitment da produzioni attive non completate (V1).

    Criteri di inclusione:
    - bucket = active (sync_produzioni_attive, attivo=True)
    - stato = "attiva" (non completata, nessun override forza_completata)
    - materiale_partenza_codice valorizzato (MAT_COD)
    - materiale_partenza_per_pezzo > 0 (MM_PEZZO)
    - CAT_ART1 del materiale != "0" (lookup su sync_articoli)

    Casi CAT_ART1 = "0" (materia prima in mm) esclusi V1.
    Materiali non presenti in sync_articoli esclusi (impossibile verificare CAT_ART1).

    committed_qty = materiale_partenza_per_pezzo (MM_PEZZO)
    source_reference = str(id_dettaglio)
    """
    rows = (
        session.query(
            SyncProduzioneAttiva.id_dettaglio,
            SyncProduzioneAttiva.materiale_partenza_codice,
            SyncProduzioneAttiva.materiale_partenza_per_pezzo,
        )
        .outerjoin(
            CoreProduzioneOverride,
            and_(
                CoreProduzioneOverride.id_dettaglio == SyncProduzioneAttiva.id_dettaglio,
                CoreProduzioneOverride.bucket == "active",
            ),
        )
        .join(
            SyncArticolo,
            SyncArticolo.codice_articolo == SyncProduzioneAttiva.materiale_partenza_codice,
        )
        .filter(
            # Produzioni attive
            SyncProduzioneAttiva.attivo == True,  # noqa: E712
            # Materiale valorizzato e positivo
            SyncProduzioneAttiva.materiale_partenza_codice.isnot(None),
            SyncProduzioneAttiva.materiale_partenza_per_pezzo.isnot(None),
            SyncProduzioneAttiva.materiale_partenza_per_pezzo > 0,
            # Stato "attiva" (nessun override forza_completata = True)
            or_(
                CoreProduzioneOverride.forza_completata.is_(None),
                CoreProduzioneOverride.forza_completata == False,  # noqa: E712
            ),
            or_(
                SyncProduzioneAttiva.quantita_prodotta.is_(None),
                SyncProduzioneAttiva.quantita_ordinata.is_(None),
                SyncProduzioneAttiva.quantita_prodotta < SyncProduzioneAttiva.quantita_ordinata,
            ),
            # CAT_ART1 del materiale != "0" (V1: solo pezzi, non mm)
            SyncArticolo.categoria_articolo_1.isnot(None),
            SyncArticolo.categoria_articolo_1 != "0",
        )
        .all()
    )

    return [
        CoreCommitment(
            article_code=row.materiale_partenza_codice,
            source_type=_SOURCE_TYPE_PRODUCTION,
            source_reference=str(row.id_dettaglio),
            committed_qty=Decimal(str(row.materiale_partenza_per_pezzo)),
            computed_at=computed_at,
        )
        for row in rows
    ]


# ─── Read: lista commitments per riga ────────────────────────────────────────

def list_commitments(
    session: Session,
    source_type: str | None = None,
) -> list[CommitmentItem]:
    """Restituisce tutti i commitments attivi, opzionalmente filtrati per source_type.

    Args:
        session:     sessione SQLAlchemy
        source_type: se valorizzato, filtra per provenienza (es. "customer_order", "production")
    """
    query = session.query(CoreCommitment).order_by(
        CoreCommitment.article_code,
        CoreCommitment.source_type,
        CoreCommitment.source_reference,
    )
    if source_type is not None:
        query = query.filter(CoreCommitment.source_type == source_type)

    return [_to_item(r) for r in query.all()]


# ─── Read: aggregazione per articolo ─────────────────────────────────────────

def get_commitments_by_article(
    session: Session,
    article_code: str | None = None,
) -> list[CommitmentsByArticleItem]:
    """Restituisce i commitments aggregati per article_code (tutte le provenienze).

    Args:
        session:      sessione SQLAlchemy
        article_code: se valorizzato, restituisce solo l'articolo specificato

    Restituisce lista vuota se non ci sono commitments attivi.
    """
    query = (
        session.query(
            CoreCommitment.article_code,
            func.sum(CoreCommitment.committed_qty).label("total_committed"),
            func.count(CoreCommitment.id).label("commitment_count"),
            func.max(CoreCommitment.computed_at).label("computed_at"),
        )
        .group_by(CoreCommitment.article_code)
        .order_by(CoreCommitment.article_code)
    )
    if article_code is not None:
        query = query.filter(CoreCommitment.article_code == article_code)

    return [
        CommitmentsByArticleItem(
            article_code=row.article_code,
            total_committed_qty=Decimal(str(row.total_committed)),
            commitment_count=row.commitment_count,
            computed_at=row.computed_at,
        )
        for row in query.all()
    ]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_item(row: CoreCommitment) -> CommitmentItem:
    return CommitmentItem(
        article_code=row.article_code,
        source_type=row.source_type,
        source_reference=row.source_reference,
        committed_qty=row.committed_qty,
        computed_at=row.computed_at,
    )
