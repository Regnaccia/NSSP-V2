"""Focused tests for proposal logic global config."""

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.production_proposals import (
    KNOWN_PROPOSAL_LOGICS,
    get_proposal_logic_config,
    set_proposal_logic_config,
)
from nssp_v2.core.production_proposals.logic import compute_note_fragment, compute_proposed_qty

# register metadata
from nssp_v2.core.production_proposals.models import CoreProposalLogicConfig  # noqa: F401
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def test_default_proposal_logic_config():
    engine, session = _session()
    try:
        config = get_proposal_logic_config(session)
        assert config.is_default is True
        assert config.default_logic_key == "proposal_target_pieces_v1"
        assert "proposal_target_pieces_v1" in KNOWN_PROPOSAL_LOGICS
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_legacy_alias_still_known():
    """proposal_required_qty_total_v1 rimane in KNOWN_PROPOSAL_LOGICS come alias compatibile."""
    assert "proposal_required_qty_total_v1" in KNOWN_PROPOSAL_LOGICS


def test_set_and_get_proposal_logic_config():
    engine, session = _session()
    try:
        saved = set_proposal_logic_config(
            session,
            default_logic_key="proposal_target_pieces_v1",
            logic_params_by_key={"proposal_target_pieces_v1": {}},
        )
        assert saved.is_default is False
        assert saved.default_logic_key == "proposal_target_pieces_v1"

        loaded = get_proposal_logic_config(session)
        assert loaded.default_logic_key == "proposal_target_pieces_v1"
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_compute_proposed_qty_target_pieces_v1():
    qty = compute_proposed_qty("proposal_target_pieces_v1", Decimal("42.5"), {})
    assert qty == Decimal("42.5")


def test_compute_proposed_qty_legacy_alias():
    qty = compute_proposed_qty("proposal_required_qty_total_v1", Decimal("10"), {})
    assert qty == Decimal("10")


def test_compute_note_fragment_is_none():
    """proposal_target_pieces_v1 non produce frammento testuale."""
    assert compute_note_fragment("proposal_target_pieces_v1", {}) is None


def test_compute_note_fragment_legacy_alias_is_none():
    assert compute_note_fragment("proposal_required_qty_total_v1", {}) is None


def test_full_bar_v1_in_known_logics():
    assert "proposal_full_bar_v1" in KNOWN_PROPOSAL_LOGICS


def test_compute_note_fragment_full_bar_with_bars():
    """proposal_full_bar_v1 con _bars_required nel snapshot restituisce BAR xN."""
    fragment = compute_note_fragment("proposal_full_bar_v1", {"_bars_required": 4})
    assert fragment == "BAR x4"


def test_compute_note_fragment_full_bar_fallback_is_none():
    """proposal_full_bar_v1 senza _bars_required (fallback attivo) restituisce None."""
    assert compute_note_fragment("proposal_full_bar_v1", {}) is None
