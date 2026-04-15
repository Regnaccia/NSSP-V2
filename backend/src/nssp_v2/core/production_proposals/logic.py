"""Pure proposal logic helpers."""

from dataclasses import dataclass
from decimal import Decimal
from math import ceil, floor

from nssp_v2.core.production_proposals.config import KNOWN_PROPOSAL_LOGICS


def merge_logic_params(global_params: dict, article_params: dict | None) -> dict:
    merged = dict(global_params)
    if article_params:
        merged.update(article_params)
    return merged


def resolve_final_qty(proposed_qty: Decimal, override_qty: Decimal | None) -> Decimal:
    return override_qty if override_qty is not None else proposed_qty


def propose_qty_v1(required_qty_total: Decimal, params_snapshot: dict) -> Decimal:
    _ = params_snapshot
    return required_qty_total


def compute_proposed_qty(logic_key: str, required_qty_total: Decimal, params_snapshot: dict) -> Decimal:
    """Calcola la qty proposta per la logica data.

    - proposal_target_pieces_v1: proposed_qty = required_qty_total
    - proposal_required_qty_total_v1: alias legacy, comportamento identico
    - proposal_full_bar_v1: arrotondamento a barre intere — richiede compute_full_bar_qty
      per il calcolo completo; qui restituisce required_qty_total come fallback di base
      (il contesto di arrotondamento barre e gestito da _workspace_row_from_candidate).
    """
    if logic_key not in KNOWN_PROPOSAL_LOGICS:
        raise ValueError(f"Logic non ammessa: {logic_key}")
    if logic_key in ("proposal_target_pieces_v1", "proposal_required_qty_total_v1", "proposal_full_bar_v1"):
        return propose_qty_v1(required_qty_total, params_snapshot)
    raise ValueError(f"Logic non implementata: {logic_key}")


def compute_note_fragment(logic_key: str, params_snapshot: dict) -> str | None:
    """Frammento testuale da aggiungere alla nota EasyJob per la logica data.

    - proposal_target_pieces_v1 / proposal_required_qty_total_v1: nessun frammento (None).
    - proposal_full_bar_v1: "BAR xN" se params_snapshot contiene _bars_required, altrimenti None.
    """
    if logic_key not in KNOWN_PROPOSAL_LOGICS:
        raise ValueError(f"Logic non ammessa: {logic_key}")
    if logic_key == "proposal_full_bar_v1":
        bars = params_snapshot.get("_bars_required")
        if bars is not None:
            return f"BAR x{bars}"
    return None


# ─── Full bar logic (TASK-V2-121) ────────────────────────────────────────────


@dataclass(frozen=True)
class FullBarResult:
    """Risultato del calcolo proposal_full_bar_v1.

    - proposed_qty: quantita arrotondata a barre intere (o fallback = required_qty_total)
    - bars_required: numero di barre calcolato; None se e stato attivato il fallback
    - used_fallback: True se il calcolo a barre non era applicabile e si e usato il fallback
    """

    proposed_qty: Decimal
    bars_required: int | None
    used_fallback: bool


def compute_full_bar_qty(
    required_qty_total: Decimal,
    customer_shortage_qty: Decimal | None,
    availability_qty: Decimal | None,
    capacity_effective_qty: Decimal | None,
    raw_bar_length_mm: Decimal | None,
    occorrente: Decimal | None,
    scarto: Decimal | None,
) -> FullBarResult:
    """Calcola la quantita proposta con arrotondamento a barre intere.

    Formula:
        usable_mm_per_piece = occorrente + (scarto or 0)
        pieces_per_bar      = floor(raw_bar_length_mm / usable_mm_per_piece)
        bars_required       = ceil(required_qty_total / pieces_per_bar)
        proposed_qty        = bars_required * pieces_per_bar

    Fallback a required_qty_total (invariato) nei seguenti casi:
        - raw_bar_length_mm is None
        - occorrente is None
        - usable_mm_per_piece <= 0
        - pieces_per_bar <= 0
        - proposed_qty < customer_shortage_qty  (sotto-copertura cliente)
        - availability_qty + proposed_qty > capacity_effective_qty  (overflow capienza)
    """

    def _fallback() -> FullBarResult:
        return FullBarResult(
            proposed_qty=required_qty_total,
            bars_required=None,
            used_fallback=True,
        )

    # Config mancante
    if raw_bar_length_mm is None or occorrente is None:
        return _fallback()

    scarto_val = scarto if scarto is not None else Decimal("0")
    usable_mm_per_piece = occorrente + scarto_val

    if usable_mm_per_piece <= Decimal("0"):
        return _fallback()

    pieces_per_bar = int(floor(float(raw_bar_length_mm / usable_mm_per_piece)))

    if pieces_per_bar <= 0:
        return _fallback()

    bars_required = int(ceil(float(required_qty_total / pieces_per_bar)))
    proposed_qty = Decimal(bars_required * pieces_per_bar)

    # Sotto-copertura cliente: proposed_qty non deve essere inferiore a customer_shortage_qty
    if customer_shortage_qty is not None and proposed_qty < customer_shortage_qty:
        return _fallback()

    # Controllo capienza: availability_qty + proposed_qty <= capacity_effective_qty
    if capacity_effective_qty is not None:
        effective_avail = availability_qty if availability_qty is not None else Decimal("0")
        if effective_avail + proposed_qty > capacity_effective_qty:
            return _fallback()

    return FullBarResult(
        proposed_qty=proposed_qty,
        bars_required=bars_required,
        used_fallback=False,
    )
