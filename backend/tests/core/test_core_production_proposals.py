"""Focused tests for proposal workspaces and exported proposal history."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem
from nssp_v2.core.production_proposals import (
    abandon_proposal_workspace,
    export_proposal_workspace_csv,
    generate_proposal_workspace,
    get_production_proposal_detail,
    get_proposal_workspace_detail,
    list_production_proposals,
    reconcile_production_proposals,
    set_proposal_workspace_row_override,
)

# register metadata
from nssp_v2.core.production_proposals.models import (  # noqa: F401
    CoreProductionProposal,
    CoreProductionProposalExportBatch,
    CoreProposalLogicConfig,
    CoreProposalWorkspace,
    CoreProposalWorkspaceRow,
)
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica  # noqa: F401


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


def _candidate(
    article_code: str = "ART001",
    planning_mode: str | None = "by_article",
    required_qty_minimum: Decimal = Decimal("10"),
    required_qty_total: Decimal | None = Decimal("15"),
    primary_driver: str | None = "customer",
    source_candidate_id: str | None = None,
    order_reference: str | None = None,
    line_reference: int | None = None,
) -> PlanningCandidateItem:
    source_id = source_candidate_id or (
        f"by_article::{article_code}"
        if planning_mode == "by_article"
        else f"by_customer_order_line::{article_code}::{order_reference or ''}::{line_reference or ''}"
    )
    return PlanningCandidateItem(
        source_candidate_id=source_id,
        article_code=article_code,
        display_label=f"Label {article_code}",
        famiglia_code=None,
        famiglia_label=None,
        effective_considera_in_produzione=True,
        effective_aggrega_codice_in_produzione=True if planning_mode == "by_article" else False,
        planning_mode=planning_mode,  # type: ignore[arg-type]
        reason_code="future_availability_negative",
        reason_text="shortage",
        description_parts=["Parte 1", "Parte 2"],
        display_description="Parte 1 Parte 2",
        active_warning_codes=["INVALID_STOCK_CAPACITY"],
        active_warnings=[],
        misura="NR",
        required_qty_minimum=required_qty_minimum,
        primary_driver=primary_driver,  # type: ignore[arg-type]
        requested_destination_display="Cliente X",
        computed_at=_NOW,
        availability_qty=Decimal("-5") if planning_mode == "by_article" else None,
        customer_open_demand_qty=Decimal("20") if planning_mode == "by_article" else None,
        incoming_supply_qty=Decimal("5") if planning_mode == "by_article" else None,
        future_availability_qty=Decimal("-5") if planning_mode == "by_article" else None,
        customer_shortage_qty=Decimal("5") if planning_mode == "by_article" else None,
        stock_replenishment_qty=Decimal("10") if planning_mode == "by_article" else None,
        required_qty_total=required_qty_total,
        is_within_customer_horizon=True if planning_mode == "by_article" else None,
        earliest_customer_delivery_date=date(2026, 4, 30) if planning_mode == "by_article" else None,
        nearest_delivery_date=date(2026, 4, 30) if planning_mode == "by_article" else None,
        order_reference=order_reference,
        line_reference=line_reference,
        order_line_description="Riga ordine" if planning_mode == "by_customer_order_line" else None,
        full_order_line_description="Riga ordine completa" if planning_mode == "by_customer_order_line" else None,
        requested_delivery_date=date(2026, 4, 18) if planning_mode == "by_customer_order_line" else None,
        line_open_demand_qty=Decimal("10") if planning_mode == "by_customer_order_line" else None,
        linked_incoming_supply_qty=Decimal("0") if planning_mode == "by_customer_order_line" else None,
        line_future_coverage_qty=Decimal("-10") if planning_mode == "by_customer_order_line" else None,
    )


def test_generate_workspace_from_by_article(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    assert result.created_count == 1
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.status == "open"
    assert len(detail.rows) == 1
    assert detail.rows[0].required_qty_total == Decimal("15")
    assert detail.rows[0].proposed_qty == Decimal("15")
    assert detail.rows[0].final_qty == Decimal("15")


def test_generate_workspace_falls_back_to_minimum_for_by_customer_order_line(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [
            _candidate(
                article_code="ART002",
                planning_mode="by_customer_order_line",
                required_qty_minimum=Decimal("7"),
                required_qty_total=None,
                source_candidate_id="by_customer_order_line::ART002::CO-1::1",
                order_reference="CO-1",
                line_reference=1,
            )
        ],
    )
    result = generate_proposal_workspace(session, ["by_customer_order_line::ART002::CO-1::1"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.rows[0].required_qty_total == Decimal("7")
    assert detail.rows[0].proposed_qty == Decimal("7")


def test_workspace_override_updates_final_qty(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    updated = set_proposal_workspace_row_override(
        session,
        workspace_id=result.workspace_id,
        row_id=detail.rows[0].row_id,
        override_qty=Decimal("99"),
        override_reason="manuale",
    )
    assert updated.rows[0].override_qty == Decimal("99")
    assert updated.rows[0].final_qty == Decimal("99")


def test_workspace_is_frozen_after_planning_changes(monkeypatch, session: Session):
    state = {"qty": Decimal("15")}

    def _loader(*args, **kwargs):
        return [_candidate(required_qty_total=state["qty"])]

    monkeypatch.setattr("nssp_v2.core.production_proposals.queries.list_planning_candidates_v1", _loader)
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    state["qty"] = Decimal("40")
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.rows[0].required_qty_total == Decimal("15")
    assert detail.rows[0].proposed_qty == Decimal("15")


def test_abandon_workspace_marks_status(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    abandon_proposal_workspace(session, result.workspace_id)
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.status == "abandoned"


def test_export_workspace_persists_exported_snapshots_and_csv(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    export_result, csv_text = export_proposal_workspace_csv(session, result.workspace_id)
    assert export_result.exported_count == 1
    assert export_result.workspace_id == result.workspace_id
    proposals = list_production_proposals(session)
    assert len(proposals) == 1
    assert proposals[0].workflow_status == "exported"
    assert proposals[0].workspace_id == result.workspace_id
    assert proposals[0].ode_ref in csv_text
    assert "note_articolo" in csv_text
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.status == "exported"


def test_reconcile_exported_proposals_via_ode_ref(monkeypatch, session: Session):
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    export_proposal_workspace_csv(session, result.workspace_id)
    proposal = list_production_proposals(session)[0]

    session.add(
        SyncProduzioneAttiva(
            id_dettaglio=1,
            codice_articolo=proposal.article_code,
            note_articolo=f"import {proposal.ode_ref}",
            attivo=True,
            synced_at=_NOW,
        )
    )
    session.commit()

    reconcile_result = reconcile_production_proposals(session, [proposal.proposal_id])
    assert reconcile_result.matched == 1
    updated = get_production_proposal_detail(session, proposal.proposal_id)
    assert updated is not None
    assert updated.workflow_status == "reconciled"
    assert updated.reconciled_production_id_dettaglio == 1


# ─── Test export-preview contract (TASK-V2-115) ───────────────────────────────

def _add_sync_articolo(
    session: Session,
    codice: str = "ART001",
    codice_immagine: str | None = "IMG",
    materiale: str | None = "MAT001",
    mm_materiale: float | None = 1.5,
    scarto_materiale: float | None = None,
) -> SyncArticolo:
    art = SyncArticolo(
        codice_articolo=codice,
        codice_immagine=codice_immagine,
        materiale_grezzo_codice=materiale,
        quantita_materiale_grezzo_occorrente=Decimal(str(mm_materiale)) if mm_materiale is not None else None,
        quantita_materiale_grezzo_scarto=Decimal(str(scarto_materiale)) if scarto_materiale is not None else None,
        attivo=True,
        synced_at=_NOW,
    )
    session.add(art)
    session.flush()
    return art


def test_workspace_row_description_parts_snapshot(monkeypatch, session: Session):
    """description_parts vengono snapshotted nel workspace row."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.description_parts == ["Parte 1", "Parte 2"]
    assert row.export_description == repr(["Parte 1", "Parte 2"])


def test_workspace_row_articolo_preview_from_sync(monkeypatch, session: Session):
    """codice_immagine, materiale, mm_materiale vengono letti da sync_articoli."""
    _add_sync_articolo(session, codice="ART001", codice_immagine="X99", materiale="ACCA", mm_materiale=2.5)
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.codice_immagine == "X99"
    assert row.materiale == "ACCA"
    assert row.mm_materiale == Decimal("2.5")


def test_workspace_row_mm_materiale_includes_scarto(monkeypatch, session: Session):
    """mm_materiale preview = occorrente + scarto."""
    _add_sync_articolo(
        session,
        codice="ART001",
        codice_immagine="X99",
        materiale="ACCA",
        mm_materiale=2.5,
        scarto_materiale=0.4,
    )
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.rows[0].mm_materiale == Decimal("2.9")


def test_workspace_row_preview_case_insensitive_sync_lookup(monkeypatch, session: Session):
    """La preview articolo usa lookup case-insensitive verso sync_articoli."""
    _add_sync_articolo(session, codice="art001", codice_immagine="X99", materiale="ACCA", mm_materiale=2.5)
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate(article_code="ART001")],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.article_code == "art001"
    assert row.codice_immagine == "X99"
    assert row.materiale == "ACCA"


def test_workspace_row_articolo_preview_missing_sync(monkeypatch, session: Session):
    """Se sync_articoli non ha il codice, i campi preview sono None."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.codice_immagine is None
    assert row.materiale is None
    assert row.mm_materiale is None


def test_ordine_customer_driver(monkeypatch, session: Session):
    """ordine = order_reference per driver customer."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [
            _candidate(
                article_code="ART001",
                planning_mode="by_customer_order_line",
                primary_driver="customer",
                source_candidate_id="by_customer_order_line::ART001::ORD-42::5",
                order_reference="ORD-42",
                line_reference=5,
                required_qty_total=None,
            )
        ],
    )
    result = generate_proposal_workspace(
        session, ["by_customer_order_line::ART001::ORD-42::5"]
    )
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.ordine == "ORD-42"
    assert row.ordine_linea_mancante is False


def test_ordine_stock_only_is_none(monkeypatch, session: Session):
    """ordine = None per candidate stock-only."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [
            _candidate(
                article_code="ART001",
                planning_mode="by_article",
                primary_driver="stock",
            )
        ],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.ordine is None
    assert row.ordine_linea_mancante is False


def test_ordine_linea_mancante_customer_no_line_ref(monkeypatch, session: Session):
    """ordine_linea_mancante = True se customer ma line_reference assente."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [
            _candidate(
                article_code="ART001",
                planning_mode="by_article",
                primary_driver="customer",
                order_reference=None,
                line_reference=None,
            )
        ],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.ordine_linea_mancante is True


def test_note_preview_contains_business_prefix_for_workspace(monkeypatch, session: Session):
    """note_preview nel workspace mostra almeno la business note deterministica."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    assert detail.rows[0].note_preview == "CONS: 30/04/2026"


def test_workspace_row_logic_key_uses_effective_fallback_logic(monkeypatch, session: Session):
    """Se full-bar fa fallback, il workspace espone la logica effettivamente usata."""
    session.add(
        CoreArticoloConfig(
            codice_articolo="ART001",
            updated_at=_NOW,
            proposal_logic_key="proposal_full_bar_v1",
            proposal_logic_article_params_json={},
        )
    )
    session.commit()
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.proposal_logic_key == "proposal_target_pieces_v1"
    assert row.proposed_qty == Decimal("15")
    assert detail.rows[0].user_preview == "NSSP"


def test_note_preview_is_ode_ref_for_exported_proposal(monkeypatch, session: Session):
    """note_preview = ode_ref per proposal esportate."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    export_proposal_workspace_csv(session, result.workspace_id)
    proposals = list_production_proposals(session)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.note_preview == proposal.ode_ref
    assert proposal.user_preview == "NSSP"


def test_export_preview_propagates_through_export(monkeypatch, session: Session):
    """description_parts vengono copiati nella proposal esportata."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    export_proposal_workspace_csv(session, result.workspace_id)
    proposals = list_production_proposals(session)
    assert proposals[0].description_parts == ["Parte 1", "Parte 2"]
    assert proposals[0].export_description == repr(["Parte 1", "Parte 2"])


# ─── Test diagnostica logica proposal (TASK-V2-124) ───────────────────────────


def test_diagnostics_no_bar_logic_requested_equals_effective(monkeypatch, session: Session):
    """Per logica non-bar, requested == effective e fallback_reason e None."""
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    # Con logica globale default (proposal_target_pieces_v1), non c'e fallback
    assert row.requested_proposal_logic_key == row.effective_proposal_logic_key
    assert row.proposal_fallback_reason is None


def test_diagnostics_full_bar_fallback_missing_raw_bar_length(monkeypatch, session: Session):
    """proposal_full_bar_v1 senza raw_bar_length_mm → fallback con reason missing_raw_bar_length."""
    session.add(
        CoreArticoloConfig(
            codice_articolo="ART001",
            updated_at=_NOW,
            proposal_logic_key="proposal_full_bar_v1",
            proposal_logic_article_params_json={},
        )
    )
    session.commit()
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate()],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.requested_proposal_logic_key == "proposal_full_bar_v1"
    assert row.effective_proposal_logic_key == "proposal_target_pieces_v1"
    assert row.proposal_fallback_reason == "missing_raw_bar_length"


def test_diagnostics_full_bar_success_no_fallback(monkeypatch, session: Session):
    """proposal_full_bar_v1 con dati completi → no fallback, diagnostics coerenti.

    raw_bar_length_mm risiede sul materiale grezzo (TASK-V2-126):
    - ART001 (finito): materiale_grezzo_codice="MAT001", occorrente=50, scarto=2
    - MAT001 (materia prima): raw_bar_length_mm=3000
    """
    # Config finito: logica full_bar, senza raw_bar_length_mm (sta sul grezzo)
    session.add(
        CoreArticoloConfig(
            codice_articolo="ART001",
            updated_at=_NOW,
            proposal_logic_key="proposal_full_bar_v1",
            proposal_logic_article_params_json={},
        )
    )
    # SyncArticolo finito con puntamento al materiale grezzo e dati di lavorazione
    session.add(
        SyncArticolo(
            codice_articolo="ART001",
            attivo=True,
            synced_at=_NOW,
            materiale_grezzo_codice="MAT001",
            quantita_materiale_grezzo_occorrente=Decimal("50"),
            quantita_materiale_grezzo_scarto=Decimal("2"),
        )
    )
    # CoreArticoloConfig del materiale grezzo con raw_bar_length_mm
    session.add(
        CoreArticoloConfig(
            codice_articolo="MAT001",
            updated_at=_NOW,
            raw_bar_length_mm=Decimal("3000"),
        )
    )
    session.commit()

    # capacity_effective_qty None → no overflow check
    monkeypatch.setattr(
        "nssp_v2.core.stock_policy.list_stock_metrics_v1",
        lambda session: [],
    )
    monkeypatch.setattr(
        "nssp_v2.core.production_proposals.queries.list_planning_candidates_v1",
        lambda *args, **kwargs: [_candidate(required_qty_total=Decimal("10"))],
    )
    result = generate_proposal_workspace(session, ["by_article::ART001"])
    detail = get_proposal_workspace_detail(session, result.workspace_id)
    assert detail is not None
    row = detail.rows[0]
    assert row.requested_proposal_logic_key == "proposal_full_bar_v1"
    assert row.effective_proposal_logic_key == "proposal_full_bar_v1"
    assert row.proposal_fallback_reason is None
    # La logica ha arrotondato: pieces_per_bar = floor(3000/52) = 57, bars = ceil(10/57) = 1
    assert row.proposed_qty == Decimal("57")
