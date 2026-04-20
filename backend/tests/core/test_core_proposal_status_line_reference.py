"""
Test `proposal_status` semantics per il campo `line_reference` — TASK-V2-155.

Regola corretta (dopo fix TASK-V2-155):
- by_customer_order_line senza line_reference → Error (ordine_linea_mancante)
- by_article (anche con primary_driver=customer) senza line_reference → NON Error
  (aggregato: line_reference assente è normale, non bloccante)
- by_customer_order_line con line_reference → non bloccato da questa regola

Copertura:
- caso by_article customer driver, line_reference assente → Valid for export
- caso by_article stock driver, line_reference assente → Valid for export
- caso by_customer_order_line, line_reference assente → Error
- caso by_customer_order_line, line_reference presente → Valid for export
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from nssp_v2.core.planning_candidates.queries import _compute_proposal_preview_v1
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem


# ─── Helper factory ───────────────────────────────────────────────────────────

def _make_logic_config(
    default_logic_key: str = "proposal_target_pieces_v1",
) -> object:
    return SimpleNamespace(
        default_logic_key=default_logic_key,
        logic_params_by_key={},
    )


def _make_item(
    *,
    planning_mode: str,
    primary_driver: str | None = None,
    line_reference: int | None = None,
    required_qty_minimum: str = "10",
    required_qty_total: str | None = "10",
) -> PlanningCandidateItem:
    """Costruisce un PlanningCandidateItem minimale con model_construct (skip validation)."""
    from datetime import datetime
    return PlanningCandidateItem.model_construct(
        source_candidate_id="test-id",
        article_code="ART001",
        display_label="ART001",
        famiglia_code=None,
        famiglia_label=None,
        effective_considera_in_produzione=True,
        effective_aggrega_codice_in_produzione=True,
        planning_mode=planning_mode,
        reason_code="test",
        reason_text="test",
        description_parts=[],
        display_description="Test",
        active_warning_codes=[],
        active_warnings=[],
        misura=None,
        required_qty_minimum=Decimal(required_qty_minimum),
        primary_driver=primary_driver,
        requested_destination_display=None,
        computed_at=datetime.now(),
        priority_score=None,
        priority_band=None,
        stock_effective_qty=Decimal("100"),
        availability_qty=Decimal("0"),
        customer_open_demand_qty=Decimal("10") if primary_driver == "customer" else None,
        incoming_supply_qty=Decimal("0"),
        future_availability_qty=Decimal("-10") if primary_driver == "customer" else None,
        customer_shortage_qty=Decimal("10") if primary_driver == "customer" else None,
        stock_replenishment_qty=Decimal("10") if primary_driver == "stock" else None,
        required_qty_total=Decimal(required_qty_total) if required_qty_total is not None else None,
        target_stock_qty=Decimal("50") if primary_driver == "stock" else None,
        is_within_customer_horizon=None,
        earliest_customer_delivery_date=None,
        nearest_delivery_date=None,
        required_qty_eventual=Decimal(required_qty_total) if required_qty_total is not None else None,
        capacity_headroom_now_qty=Decimal("50"),
        release_qty_now_max=Decimal("10"),
        release_status="launchable_now",
        open_order_lines=[],
        proposal_status=None,
        proposal_qty_computed=None,
        requested_proposal_logic_key=None,
        effective_proposal_logic_key=None,
        proposal_fallback_reason=None,
        proposal_reason_summary=None,
        proposal_local_warnings=[],
        note_fragment=None,
        order_reference="ORD001" if planning_mode == "by_customer_order_line" else None,
        line_reference=line_reference,
        order_line_description=None,
        full_order_line_description=None,
        requested_delivery_date=None,
        line_open_demand_qty=Decimal("10") if planning_mode == "by_customer_order_line" else None,
        linked_incoming_supply_qty=Decimal("0") if planning_mode == "by_customer_order_line" else None,
        line_future_coverage_qty=Decimal("-10") if planning_mode == "by_customer_order_line" else None,
    )


# ─── Test class ───────────────────────────────────────────────────────────────

class TestProposalStatusLineReferenceSemantics:
    """
    Verifica che ordine_linea_mancante si applichi solo a by_customer_order_line.
    TASK-V2-155: by_article non deve essere bloccato dall'assenza di line_reference.
    """

    def test_by_article_customer_driver_no_line_reference_not_error(self) -> None:
        """
        by_article con primary_driver=customer e line_reference=None:
        deve essere Valid for export, NON Error.
        In by_article la mancanza di line_reference è attesa (candidate aggregato).
        """
        item = _make_item(
            planning_mode="by_article",
            primary_driver="customer",
            line_reference=None,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert result.proposal_status == "Valid for export", (
            f"by_article customer senza line_reference non deve essere Error, "
            f"ma ha status={result.proposal_status!r}"
        )

    def test_by_article_stock_driver_no_line_reference_not_error(self) -> None:
        """
        by_article con primary_driver=stock e line_reference=None:
        deve essere Valid for export (stock-only non ha mai line_reference).
        """
        item = _make_item(
            planning_mode="by_article",
            primary_driver="stock",
            line_reference=None,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert result.proposal_status == "Valid for export", (
            f"by_article stock senza line_reference non deve essere Error, "
            f"ma ha status={result.proposal_status!r}"
        )

    def test_by_customer_order_line_missing_line_reference_is_error(self) -> None:
        """
        by_customer_order_line con line_reference=None:
        deve essere Error (ordine_linea_mancante — blocca export XLSX).
        """
        item = _make_item(
            planning_mode="by_customer_order_line",
            primary_driver="customer",
            line_reference=None,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert result.proposal_status == "Error", (
            f"by_customer_order_line senza line_reference deve essere Error, "
            f"ma ha status={result.proposal_status!r}"
        )

    def test_by_customer_order_line_with_line_reference_not_error(self) -> None:
        """
        by_customer_order_line con line_reference valorizzato:
        ordine_linea_mancante non si attiva → Valid for export.
        """
        item = _make_item(
            planning_mode="by_customer_order_line",
            primary_driver="customer",
            line_reference=3,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert result.proposal_status == "Valid for export", (
            f"by_customer_order_line con line_reference presente non deve essere Error, "
            f"ma ha status={result.proposal_status!r}"
        )

    def test_error_reason_summary_for_missing_line_reference(self) -> None:
        """
        Quando ordine_linea_mancante si attiva, il reason_summary deve indicare
        la riga ordine mancante.
        """
        item = _make_item(
            planning_mode="by_customer_order_line",
            primary_driver="customer",
            line_reference=None,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert "mancante" in result.proposal_reason_summary.lower(), (
            f"reason_summary deve menzionare riga mancante, "
            f"trovato: {result.proposal_reason_summary!r}"
        )

    def test_by_article_customer_reason_summary_contains_qty(self) -> None:
        """
        by_article con customer driver e logic target_pieces:
        reason_summary deve contenere la qty (non il messaggio di errore riga).
        """
        item = _make_item(
            planning_mode="by_article",
            primary_driver="customer",
            line_reference=None,
        )
        result = _compute_proposal_preview_v1(
            item, None, _make_logic_config(), {}, {}
        )
        assert "qty:" in result.proposal_reason_summary.lower(), (
            f"reason_summary per by_article deve contenere qty, "
            f"trovato: {result.proposal_reason_summary!r}"
        )
