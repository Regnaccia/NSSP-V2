"""
Query del Core slice `ordini_cliente` (TASK-V2-041, DL-ARCH-V2-018).

Regole:
- legge da sync_righe_ordine_cliente (mai da Easy direttamente)
- non introduce tabelle Core aggiuntive: il Core e un layer di lettura e calcolo
- nessuna logica di modulo locale
- nessuna duplicazione persistente di dati cliente/destinazione

Formula open_qty (V1):
    open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
    valori None trattati come 0.

Aggregazione description_lines:
    Le righe sync con continues_previous_line=True immediatamente successive
    vengono raccolte in description_lines della riga principale precedente.
    Non generano CustomerOrderLineItem autonomi.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from nssp_v2.core.ordini_cliente.read_models import CustomerOrderLineItem
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente


# ─── Helper: calcolo open_qty ─────────────────────────────────────────────────

def _compute_open_qty(
    ordered_qty: Decimal | None,
    set_aside_qty: Decimal | None,
    fulfilled_qty: Decimal | None,
) -> Decimal:
    """Calcola la quantita ancora aperta (V1).

    Formula: max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
    I valori None sono trattati come 0.
    Il risultato e sempre >= 0: la quantita aperta non puo essere negativa.
    """
    ordered = ordered_qty if ordered_qty is not None else Decimal("0")
    set_aside = set_aside_qty if set_aside_qty is not None else Decimal("0")
    fulfilled = fulfilled_qty if fulfilled_qty is not None else Decimal("0")
    result = ordered - set_aside - fulfilled
    return result if result > Decimal("0") else Decimal("0")


# ─── Helper: conversione row -> CustomerOrderLineItem ─────────────────────────

def _to_item(
    row: SyncRigaOrdineCliente,
    description_lines: list[str],
) -> CustomerOrderLineItem:
    return CustomerOrderLineItem(
        order_reference=row.order_reference,
        line_reference=row.line_reference,
        order_date=row.order_date,
        expected_delivery_date=row.expected_delivery_date,
        customer_order_reference=row.customer_order_reference,
        customer_code=row.customer_code,
        destination_code=row.destination_code,
        customer_destination_progressive=row.customer_destination_progressive,
        is_main_destination=not bool(row.customer_destination_progressive),
        article_code=row.article_code,
        article_measure=row.article_measure,
        article_description_segment=row.article_description_segment,
        description_lines=description_lines,
        ordered_qty=row.ordered_qty,
        fulfilled_qty=row.fulfilled_qty,
        set_aside_qty=row.set_aside_qty,
        open_qty=_compute_open_qty(row.ordered_qty, row.set_aside_qty, row.fulfilled_qty),
        net_unit_price=row.net_unit_price,
    )


# ─── Helper: aggregazione righe in CustomerOrderLineItem ─────────────────────

def _build_items(rows: list[SyncRigaOrdineCliente]) -> list[CustomerOrderLineItem]:
    """Costruisce CustomerOrderLineItem aggregando le righe descrittive di continuazione.

    Le righe con continues_previous_line=True vengono accumulate in description_lines
    della riga principale immediatamente precedente e non compaiono come item autonomi.

    L'algoritmo rispetta l'ordine dichiarato (order_reference, line_reference):
    deve essere applicato a righe gia ordinate in ingresso.
    """
    result: list[CustomerOrderLineItem] = []
    description_buffer: list[str] = []
    pending_row: SyncRigaOrdineCliente | None = None

    for row in rows:
        if row.continues_previous_line:
            # Riga di continuazione: accumula solo se appartiene allo stesso ordine
            if (
                pending_row is not None
                and row.order_reference == pending_row.order_reference
                and row.article_description_segment
            ):
                description_buffer.append(row.article_description_segment)
        else:
            # Riga principale: emetti la riga pendente (se presente)
            if pending_row is not None:
                result.append(_to_item(pending_row, description_buffer))
            pending_row = row
            description_buffer = []

    # Emetti l'ultima riga pendente
    if pending_row is not None:
        result.append(_to_item(pending_row, description_buffer))

    return result


# ─── Read model: lista tutte le righe ordine ─────────────────────────────────

def list_customer_order_lines(session: Session) -> list[CustomerOrderLineItem]:
    """Restituisce tutte le righe ordine cliente canoniche, ordinate per ordine e progressivo.

    Le righe descrittive (COLL_RIGA_PREC=True) vengono aggregate in description_lines
    della riga principale precedente e non compaiono come item autonomi.
    """
    rows = (
        session.query(SyncRigaOrdineCliente)
        .order_by(
            SyncRigaOrdineCliente.order_reference,
            SyncRigaOrdineCliente.line_reference,
        )
        .all()
    )
    return _build_items(rows)


# ─── Read model: righe di un singolo ordine ──────────────────────────────────

def get_order_lines_by_order(
    session: Session,
    order_reference: str,
) -> list[CustomerOrderLineItem]:
    """Restituisce le righe canoniche di un singolo ordine cliente.

    Restituisce lista vuota se l'ordine non esiste nel mirror.
    """
    rows = (
        session.query(SyncRigaOrdineCliente)
        .filter(SyncRigaOrdineCliente.order_reference == order_reference)
        .order_by(SyncRigaOrdineCliente.line_reference)
        .all()
    )
    return _build_items(rows)


# ─── Read model: singola riga ordine ─────────────────────────────────────────

def get_order_line(
    session: Session,
    order_reference: str,
    line_reference: int,
) -> CustomerOrderLineItem | None:
    """Restituisce la riga ordine canonica identificata da (order_reference, line_reference).

    Restituisce None se:
    - la riga non esiste nel mirror
    - la riga e essa stessa una riga di continuazione (continues_previous_line=True):
      le righe di continuazione non sono entita canoniche autonome

    Le description_lines includono le righe COLL_RIGA_PREC=True immediatamente successive.
    """
    # Legge la riga richiesta + tutte le successive dello stesso ordine
    # per raccogliere le eventuali righe di continuazione
    rows = (
        session.query(SyncRigaOrdineCliente)
        .filter(
            SyncRigaOrdineCliente.order_reference == order_reference,
            SyncRigaOrdineCliente.line_reference >= line_reference,
        )
        .order_by(SyncRigaOrdineCliente.line_reference)
        .all()
    )

    if not rows:
        return None

    target = rows[0]
    if target.line_reference != line_reference:
        return None
    if target.continues_previous_line:
        # Le righe di continuazione non sono entita principali autonome
        return None

    # Raccoglie le description_lines dalle righe di continuazione immediate
    description_lines: list[str] = []
    for row in rows[1:]:
        if row.continues_previous_line:
            if row.article_description_segment:
                description_lines.append(row.article_description_segment)
        else:
            break  # Incontrata la riga principale successiva: stop

    return _to_item(target, description_lines)
