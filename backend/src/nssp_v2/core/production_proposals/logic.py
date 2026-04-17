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


_FULL_BAR_LOGIC_KEYS = frozenset({
    "proposal_full_bar_v1",
    "proposal_full_bar_v2_capacity_floor",
    "proposal_multi_bar_v1_capacity_floor",
})


def compute_proposed_qty(logic_key: str, required_qty_total: Decimal, params_snapshot: dict) -> Decimal:
    """Calcola la qty proposta per la logica data.

    - proposal_target_pieces_v1: proposed_qty = required_qty_total
    - proposal_required_qty_total_v1: alias legacy, comportamento identico
    - proposal_full_bar_v1 / proposal_full_bar_v2_capacity_floor /
      proposal_multi_bar_v1_capacity_floor: arrotondamento a barre intere —
      il calcolo completo e gestito da _workspace_row_from_candidate; qui restituisce
      required_qty_total come base di fallback.
    """
    if logic_key not in KNOWN_PROPOSAL_LOGICS:
        raise ValueError(f"Logic non ammessa: {logic_key}")
    if logic_key in ("proposal_target_pieces_v1", "proposal_required_qty_total_v1") or logic_key in _FULL_BAR_LOGIC_KEYS:
        return propose_qty_v1(required_qty_total, params_snapshot)
    raise ValueError(f"Logic non implementata: {logic_key}")


def compute_note_fragment(logic_key: str, params_snapshot: dict) -> str | None:
    """Frammento testuale da aggiungere alla nota EasyJob per la logica data.

    - proposal_target_pieces_v1 / proposal_required_qty_total_v1: nessun frammento (None).
    - proposal_full_bar_v1 / proposal_full_bar_v2_capacity_floor: "BAR xN" se params_snapshot
      contiene _bars_required, altrimenti None.
    - proposal_multi_bar_v1_capacity_floor: "FASCI xN" (semanticamente distinto da BAR).
    """
    if logic_key not in KNOWN_PROPOSAL_LOGICS:
        raise ValueError(f"Logic non ammessa: {logic_key}")
    if logic_key == "proposal_multi_bar_v1_capacity_floor":
        bars = params_snapshot.get("_bars_required")
        if bars is not None:
            return f"FASCI x{bars}"
    elif logic_key in _FULL_BAR_LOGIC_KEYS:
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
    - fallback_reason: codice vocabolario del motivo di fallback; None se non c'e fallback

    Vocabolario fallback_reason (TASK-V2-124):
        missing_raw_bar_length      — raw_bar_length_mm o occorrente assenti
        invalid_usable_mm_per_piece — usable_mm_per_piece <= 0
        pieces_per_bar_le_zero      — pieces_per_bar <= 0 (barra piu corta del pezzo)
        customer_undercoverage      — proposed_qty < customer_shortage_qty
        capacity_overflow           — availability_qty + proposed_qty > capacity_effective_qty
    """

    proposed_qty: Decimal
    bars_required: int | None
    used_fallback: bool
    fallback_reason: str | None = None


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
        - raw_bar_length_mm is None o occorrente is None → missing_raw_bar_length
        - usable_mm_per_piece <= 0                       → invalid_usable_mm_per_piece
        - pieces_per_bar <= 0                            → pieces_per_bar_le_zero
        - proposed_qty < customer_shortage_qty           → customer_undercoverage
        - availability_qty + proposed_qty > capacity     → capacity_overflow
    """

    def _fallback(reason: str) -> FullBarResult:
        return FullBarResult(
            proposed_qty=required_qty_total,
            bars_required=None,
            used_fallback=True,
            fallback_reason=reason,
        )

    # Config mancante
    if raw_bar_length_mm is None or occorrente is None:
        return _fallback("missing_raw_bar_length")

    scarto_val = scarto if scarto is not None else Decimal("0")
    usable_mm_per_piece = occorrente + scarto_val

    if usable_mm_per_piece <= Decimal("0"):
        return _fallback("invalid_usable_mm_per_piece")

    pieces_per_bar = int(floor(float(raw_bar_length_mm / usable_mm_per_piece)))

    if pieces_per_bar <= 0:
        return _fallback("pieces_per_bar_le_zero")

    bars_required = int(ceil(float(required_qty_total / pieces_per_bar)))
    proposed_qty = Decimal(bars_required * pieces_per_bar)

    # Sotto-copertura cliente: proposed_qty non deve essere inferiore a customer_shortage_qty
    if customer_shortage_qty is not None and proposed_qty < customer_shortage_qty:
        return _fallback("customer_undercoverage")

    # Controllo capienza: availability_qty + proposed_qty <= capacity_effective_qty
    if capacity_effective_qty is not None:
        effective_avail = availability_qty if availability_qty is not None else Decimal("0")
        if effective_avail + proposed_qty > capacity_effective_qty:
            return _fallback("capacity_overflow")

    return FullBarResult(
        proposed_qty=proposed_qty,
        bars_required=bars_required,
        used_fallback=False,
        fallback_reason=None,
    )


# ─── Full bar v2: capacity floor (TASK-V2-127) ───────────────────────────────


def compute_full_bar_qty_v2_capacity_floor(
    required_qty_total: Decimal,
    customer_shortage_qty: Decimal | None,
    availability_qty: Decimal | None,
    capacity_effective_qty: Decimal | None,
    raw_bar_length_mm: Decimal | None,
    occorrente: Decimal | None,
    scarto: Decimal | None,
) -> FullBarResult:
    """Calcola la quantita proposta con arrotondamento barre + fallback floor su overflow.

    Algoritmo:
        usable_mm_per_piece = occorrente + (scarto or 0)
        pieces_per_bar      = floor(raw_bar_length_mm / usable_mm_per_piece)
        bars_ceil           = ceil(required_qty_total / pieces_per_bar)
        qty_ceil            = bars_ceil * pieces_per_bar

        Se qty_ceil <= capacity → usa qty_ceil (identico a v1 senza overflow).
        Se qty_ceil > capacity → tenta floor:
            bars_floor = floor(required_qty_total / pieces_per_bar)
            qty_floor  = bars_floor * pieces_per_bar
            Ammesso solo se:
              - bars_floor > 0
              - qty_floor >= customer_shortage_qty  (non sotto-copre il cliente)
              - availability_qty + qty_floor <= capacity_effective_qty

    Pre-guardie (stesse di v1):
        missing_raw_bar_length      — raw_bar_length_mm o occorrente assenti
        invalid_usable_mm_per_piece — usable_mm_per_piece <= 0
        pieces_per_bar_le_zero      — pieces_per_bar <= 0
        customer_undercoverage      — qty_ceil < customer_shortage_qty
                                      (o qty_floor < customer_shortage_qty se il ceil sfora)
        capacity_overflow           — ne ceil ne floor ammissibili
    """

    def _fallback(reason: str) -> FullBarResult:
        return FullBarResult(
            proposed_qty=required_qty_total,
            bars_required=None,
            used_fallback=True,
            fallback_reason=reason,
        )

    if raw_bar_length_mm is None or occorrente is None:
        return _fallback("missing_raw_bar_length")

    scarto_val = scarto if scarto is not None else Decimal("0")
    usable_mm_per_piece = occorrente + scarto_val

    if usable_mm_per_piece <= Decimal("0"):
        return _fallback("invalid_usable_mm_per_piece")

    pieces_per_bar = int(floor(float(raw_bar_length_mm / usable_mm_per_piece)))

    if pieces_per_bar <= 0:
        return _fallback("pieces_per_bar_le_zero")

    bars_ceil = int(ceil(float(required_qty_total / pieces_per_bar)))
    qty_ceil = Decimal(bars_ceil * pieces_per_bar)

    # Sotto-copertura cliente: qty_ceil non deve essere inferiore a customer_shortage_qty
    if customer_shortage_qty is not None and qty_ceil < customer_shortage_qty:
        return _fallback("customer_undercoverage")

    effective_avail = availability_qty if availability_qty is not None else Decimal("0")

    # Se qty_ceil entra in capienza (o capienza non configurata) → usa ceil
    if capacity_effective_qty is None or effective_avail + qty_ceil <= capacity_effective_qty:
        return FullBarResult(
            proposed_qty=qty_ceil,
            bars_required=bars_ceil,
            used_fallback=False,
            fallback_reason=None,
        )

    # qty_ceil sfora → tenta floor
    bars_floor = int(floor(float(required_qty_total / pieces_per_bar)))

    if bars_floor <= 0:
        return _fallback("capacity_overflow")

    qty_floor = Decimal(bars_floor * pieces_per_bar)

    if customer_shortage_qty is not None and qty_floor < customer_shortage_qty:
        return _fallback("customer_undercoverage")

    if effective_avail + qty_floor > capacity_effective_qty:
        return _fallback("capacity_overflow")

    return FullBarResult(
        proposed_qty=qty_floor,
        bars_required=bars_floor,
        used_fallback=False,
        fallback_reason=None,
    )


# ─── Multi bar v1: capacity floor con moltiplicatore (TASK-V2-131) ────────────


def compute_multi_bar_qty_v1_capacity_floor(
    required_qty_total: Decimal,
    customer_shortage_qty: Decimal | None,
    availability_qty: Decimal | None,
    capacity_effective_qty: Decimal | None,
    raw_bar_length_mm: Decimal | None,
    occorrente: Decimal | None,
    scarto: Decimal | None,
    bar_multiple: int | None,
) -> FullBarResult:
    """Calcola la quantita proposta con moltiplicatore per barra + policy capacity_floor.

    Algoritmo:
        usable_mm_per_piece = occorrente + (scarto or 0)
        base_pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
        pieces_per_bar      = base_pieces_per_bar * bar_multiple
        bars_ceil           = ceil(required_qty_total / pieces_per_bar)
        qty_ceil            = bars_ceil * pieces_per_bar

        Se qty_ceil <= capacity → usa qty_ceil.
        Se qty_ceil > capacity → tenta floor:
            bars_floor = floor(required_qty_total / pieces_per_bar)
            qty_floor  = bars_floor * pieces_per_bar
            Ammesso solo se:
              - bars_floor > 0
              - qty_floor >= customer_shortage_qty
              - availability_qty + qty_floor <= capacity_effective_qty

    Pre-guardie aggiuntive rispetto a full_bar_v2:
        missing_bar_multiple       — bar_multiple mancante o <= 0
        pieces_per_bar_le_zero     — base_pieces_per_bar <= 0 (barra troppo corta)
    """

    def _fallback(reason: str) -> FullBarResult:
        return FullBarResult(
            proposed_qty=required_qty_total,
            bars_required=None,
            used_fallback=True,
            fallback_reason=reason,
        )

    if raw_bar_length_mm is None or occorrente is None:
        return _fallback("missing_raw_bar_length")

    if bar_multiple is None or bar_multiple <= 0:
        return _fallback("missing_bar_multiple")

    scarto_val = scarto if scarto is not None else Decimal("0")
    usable_mm_per_piece = occorrente + scarto_val

    if usable_mm_per_piece <= Decimal("0"):
        return _fallback("invalid_usable_mm_per_piece")

    base_pieces_per_bar = int(floor(float(raw_bar_length_mm / usable_mm_per_piece)))

    if base_pieces_per_bar <= 0:
        return _fallback("pieces_per_bar_le_zero")

    pieces_per_bar = base_pieces_per_bar * bar_multiple

    if pieces_per_bar <= 0:
        return _fallback("pieces_per_bar_le_zero")

    bars_ceil = int(ceil(float(required_qty_total / pieces_per_bar)))
    qty_ceil = Decimal(bars_ceil * pieces_per_bar)

    # Sotto-copertura cliente: qty_ceil non deve essere inferiore a customer_shortage_qty
    if customer_shortage_qty is not None and qty_ceil < customer_shortage_qty:
        return _fallback("customer_undercoverage")

    effective_avail = availability_qty if availability_qty is not None else Decimal("0")

    # Se qty_ceil entra in capienza (o capienza non configurata) → usa ceil
    if capacity_effective_qty is None or effective_avail + qty_ceil <= capacity_effective_qty:
        return FullBarResult(
            proposed_qty=qty_ceil,
            bars_required=bars_ceil,
            used_fallback=False,
            fallback_reason=None,
        )

    # qty_ceil sfora → tenta floor
    bars_floor = int(floor(float(required_qty_total / pieces_per_bar)))

    if bars_floor <= 0:
        return _fallback("capacity_overflow")

    qty_floor = Decimal(bars_floor * pieces_per_bar)

    if customer_shortage_qty is not None and qty_floor < customer_shortage_qty:
        return _fallback("customer_undercoverage")

    if effective_avail + qty_floor > capacity_effective_qty:
        return _fallback("capacity_overflow")

    return FullBarResult(
        proposed_qty=qty_floor,
        bars_required=bars_floor,
        used_fallback=False,
        fallback_reason=None,
    )
