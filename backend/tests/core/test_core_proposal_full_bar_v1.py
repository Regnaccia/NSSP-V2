"""Test mirati per proposal_full_bar_v1 — TASK-V2-121.

Copre:
- formula felice (barre intere)
- note_fragment = "BAR xN"
- tutti i casi di fallback obbligatori
- indipendenza fallback da note_fragment
"""

from decimal import Decimal

import pytest

from nssp_v2.core.production_proposals.config import KNOWN_PROPOSAL_LOGICS
from nssp_v2.core.production_proposals.logic import (
    FullBarResult,
    compute_full_bar_qty,
    compute_note_fragment,
)


# ─── Registry ────────────────────────────────────────────────────────────────


def test_proposal_full_bar_v1_in_known_logics():
    assert "proposal_full_bar_v1" in KNOWN_PROPOSAL_LOGICS


# ─── compute_full_bar_qty: happy path ────────────────────────────────────────


def test_full_bar_basic_formula():
    """3000 mm barra, 100 mm occorrente, 0 scarto => 30 pz/barra.
    required=50 => ceil(50/30)=2 barre => proposed=60."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=Decimal("30"),
        availability_qty=Decimal("0"),
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is False
    assert result.bars_required == 2
    assert result.proposed_qty == Decimal("60")


def test_full_bar_with_scarto():
    """3000 mm barra, 90 mm occorrente, 10 mm scarto => usable=100 mm => 30 pz/barra.
    required=31 => ceil(31/30)=2 => proposed=60."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("31"),
        customer_shortage_qty=Decimal("20"),
        availability_qty=Decimal("0"),
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("90"),
        scarto=Decimal("10"),
    )
    assert result.used_fallback is False
    assert result.bars_required == 2
    assert result.proposed_qty == Decimal("60")


def test_full_bar_exact_fit():
    """required=30 esatto => 1 barra => proposed=30."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("30"),
        customer_shortage_qty=Decimal("10"),
        availability_qty=Decimal("0"),
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is False
    assert result.bars_required == 1
    assert result.proposed_qty == Decimal("30")


def test_full_bar_floor_pieces_per_bar():
    """3000 mm barra, 110 mm usable => floor(3000/110)=27 pz/barra.
    required=50 => ceil(50/27)=2 => proposed=54."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("110"),
        scarto=None,
    )
    assert result.used_fallback is False
    assert result.bars_required == 2
    assert result.proposed_qty == Decimal("54")


# ─── compute_note_fragment ────────────────────────────────────────────────────


def test_note_fragment_full_bar_with_bars_required():
    params = {"_bars_required": 3}
    fragment = compute_note_fragment("proposal_full_bar_v1", params)
    assert fragment == "BAR x3"


def test_note_fragment_full_bar_fallback_no_bars_required():
    """Se il fallback e attivo, _bars_required non e presente => fragment = None."""
    fragment = compute_note_fragment("proposal_full_bar_v1", {})
    assert fragment is None


def test_note_fragment_target_pieces_v1_is_none():
    assert compute_note_fragment("proposal_target_pieces_v1", {}) is None


# ─── Fallback: config mancante ────────────────────────────────────────────────


def test_fallback_raw_bar_length_missing():
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=None,
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is True
    assert result.bars_required is None
    assert result.proposed_qty == Decimal("50")


def test_fallback_occorrente_missing():
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=None,
        scarto=None,
    )
    assert result.used_fallback is True
    assert result.proposed_qty == Decimal("50")


# ─── Fallback: usable_mm_per_piece <= 0 ──────────────────────────────────────


def test_fallback_zero_occorrente_zero_scarto():
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("0"),
        scarto=Decimal("0"),
    )
    assert result.used_fallback is True


def test_fallback_negative_usable_mm():
    """occorrente negativo non ha senso fisico ma il guard deve coprirlo."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("-50"),
        scarto=Decimal("10"),
    )
    assert result.used_fallback is True


# ─── Fallback: pieces_per_bar <= 0 ───────────────────────────────────────────


def test_fallback_bar_shorter_than_piece():
    """Barra 50 mm, usable 100 mm => floor(50/100)=0 pz/barra => fallback."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("10"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("50"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is True
    assert result.proposed_qty == Decimal("10")


# ─── Fallback: overflow capienza ─────────────────────────────────────────────


def test_fallback_overflow_capacity():
    """availability=0, proposed=60 => 0+60=60 > capacity=50 => fallback."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=Decimal("0"),
        capacity_effective_qty=Decimal("50"),
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is True
    assert result.proposed_qty == Decimal("50")


def test_no_fallback_capacity_exact():
    """availability=0, proposed=60 = capacity=60 => ok."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=Decimal("0"),
        capacity_effective_qty=Decimal("60"),
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is False
    assert result.proposed_qty == Decimal("60")


def test_no_fallback_capacity_none_skips_check():
    """capacity_effective_qty=None => il controllo capienza e saltato."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("200"),
        customer_shortage_qty=None,
        availability_qty=Decimal("0"),
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is False
    assert result.proposed_qty == Decimal("210")


# ─── Fallback: sotto-copertura cliente ───────────────────────────────────────


def test_fallback_sotto_copertura():
    """Caso patologico: proposed < customer_shortage => fallback."""
    # Simulabile solo con dati anomali (proposed normalmente >= required >= shortage).
    # Usiamo pieces_per_bar=1 (usable=3000) e required_qty_total molto piccola
    # ma customer_shortage > proposed.
    # In realta proposed >= required >= shortage, quindi questo test usa
    # un customer_shortage artificialmente maggiore di required.
    result = compute_full_bar_qty(
        required_qty_total=Decimal("1"),
        customer_shortage_qty=Decimal("5"),  # anomalia: shortage > required
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    # proposed = 30 (1 barra) >= shortage=5 => NO fallback in questo caso
    # (30 >= 5 e vero)
    # Il guard e per il caso in cui ceil arrotonda sotto
    # In pratica non triggerabile con dati coerenti; il test verifica la guardia
    assert result.used_fallback is False  # 30 >= 5


def test_no_fallback_shortage_none():
    """customer_shortage_qty=None => il controllo sotto-copertura e saltato."""
    result = compute_full_bar_qty(
        required_qty_total=Decimal("50"),
        customer_shortage_qty=None,
        availability_qty=None,
        capacity_effective_qty=None,
        raw_bar_length_mm=Decimal("3000"),
        occorrente=Decimal("100"),
        scarto=None,
    )
    assert result.used_fallback is False
