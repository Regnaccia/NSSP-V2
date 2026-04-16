"""Queries and state transitions for temporary proposal workspaces and exported proposal history."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import CoreArticoloConfig
from nssp_v2.core.articoli.queries import _resolve_sync_articolo_code
from nssp_v2.core.planning_candidates import PlanningCandidateItem, list_planning_candidates_v1
from nssp_v2.core.production_proposals.config import get_proposal_logic_config
from nssp_v2.core.production_proposals.logic import (
    compute_full_bar_qty,
    compute_full_bar_qty_v2_capacity_floor,
    compute_note_fragment,
    compute_proposed_qty,
    merge_logic_params,
    resolve_final_qty,
)
from nssp_v2.core.production_proposals.models import (
    CoreProductionProposal,
    CoreProductionProposalExportBatch,
    CoreProposalWorkspace,
    CoreProposalWorkspaceRow,
)
from nssp_v2.core.production_proposals.read_models import (
    ProductionProposalDetail,
    ProductionProposalExportBatchResult,
    ProductionProposalItem,
    ProductionProposalReconcileResult,
    ProposalWorkspaceDetail,
    ProposalWorkspaceGenerateResult,
    ProposalWorkspaceRowItem,
)
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica

_WORKSPACE_TTL_HOURS = 8

_USER_PREVIEW = "NSSP"


# ─── Export preview helpers (TASK-V2-115) ─────────────────────────────────────

@dataclass
class _ArticoloPreview:
    codice_immagine: str | None
    materiale: str | None
    mm_materiale: Decimal | None


def _load_articolo_preview_data(
    session: Session,
    article_codes: set[str],
) -> dict[str, _ArticoloPreview]:
    """Batch-load dei campi anagrafici export-preview da sync_articoli.

    Restituisce mappa article_code (upper/stripped) -> _ArticoloPreview.
    """
    if not article_codes:
        return {}
    rows = session.scalars(
        select(SyncArticolo).where(
            func.upper(func.trim(SyncArticolo.codice_articolo)).in_(article_codes)
        )
    ).all()
    result: dict[str, _ArticoloPreview] = {}
    for art in rows:
        key = art.codice_articolo.strip().upper()
        mm_materiale = art.quantita_materiale_grezzo_occorrente
        if mm_materiale is not None:
            mm_materiale = mm_materiale + (art.quantita_materiale_grezzo_scarto or Decimal("0"))
        result[key] = _ArticoloPreview(
            codice_immagine=(art.codice_immagine or "").strip() or None,
            materiale=(art.materiale_grezzo_codice or "").strip() or None,
            mm_materiale=mm_materiale,
        )
    return result


def _export_description(description_parts: list[str]) -> str:
    """Serializzazione Python-list-repr per colonna EasyJob (es. ['Parte 1', 'Parte 2']).

    E la forma che viene scritta nella cella Excel EasyJob per le righe multilinea.
    """
    return repr(description_parts)


def _workspace_note_preview(
    requested_delivery_date,
    proposal_logic_key: str,
    params_snapshot: dict,
) -> str:
    parts: list[str] = []
    if requested_delivery_date is not None:
        parts.append(f"CONS: {requested_delivery_date.strftime('%d/%m/%Y')}")
    logic_fragment = compute_note_fragment(proposal_logic_key, params_snapshot)
    if logic_fragment:
        parts.append(logic_fragment)
    return " | ".join(parts)


def _ordine_from_row(
    primary_driver: str | None,
    planning_mode: str | None,
    order_reference: str | None,
) -> str | None:
    """Numero ordine da includere nel tracciato EasyJob.

    - driver customer o ramo by_customer_order_line → order_reference (stringa, anche vuota)
    - stock-only → None (campo vuoto nel tracciato)
    """
    if primary_driver == "customer" or planning_mode == "by_customer_order_line":
        return order_reference or ""
    return None


def _ordine_linea_mancante(
    primary_driver: str | None,
    planning_mode: str | None,
    line_reference: int | None,
) -> bool:
    """True se il candidate e customer-driven ma manca il riferimento riga ordine.

    Indica un errore semantico bloccante per il futuro writer xlsx.
    """
    if primary_driver == "customer" or planning_mode == "by_customer_order_line":
        return line_reference is None
    return False


def _canonical_required_qty_total(item: PlanningCandidateItem) -> Decimal:
    if item.required_qty_total is not None:
        return item.required_qty_total
    return item.required_qty_minimum


def _resolve_article_proposal_config(
    session: Session,
    article_code: str,
) -> tuple[str | None, dict]:
    resolved = _resolve_sync_articolo_code(session, article_code) or article_code
    cfg = session.get(CoreArticoloConfig, resolved)
    if cfg is None:
        return None, {}
    return cfg.proposal_logic_key, dict(cfg.proposal_logic_article_params_json or {})


def _resolve_full_bar_proposed_qty(
    session: Session,
    item: PlanningCandidateItem,
    required_qty_total: Decimal,
    params_snapshot: dict,
    logic_key: str = "proposal_full_bar_v1",
) -> tuple[Decimal, dict, bool, str | None]:
    """Calcola proposed_qty per le logiche full-bar e arricchisce params_snapshot con _bars_required.

    Gestisce: proposal_full_bar_v1, proposal_full_bar_v2_capacity_floor.
    Restituisce (proposed_qty, params_snapshot_aggiornato, used_fallback, fallback_reason).
    In caso di fallback: used_fallback=True, fallback_reason e il codice motivo.
    In caso di successo: used_fallback=False, fallback_reason=None.

    raw_bar_length_mm e letto sul materiale grezzo associato al finito (TASK-V2-126):
      1. sync_art.materiale_grezzo_codice  → codice del materiale grezzo
      2. CoreArticoloConfig del materiale  → raw_bar_length_mm
    occorrente/scarto restano sul finito.
    """
    resolved_code = _resolve_sync_articolo_code(session, item.article_code) or item.article_code

    sync_art = session.scalar(
        select(SyncArticolo).where(SyncArticolo.codice_articolo == resolved_code)
    )
    occorrente = sync_art.quantita_materiale_grezzo_occorrente if sync_art else None
    scarto = sync_art.quantita_materiale_grezzo_scarto if sync_art else None

    # raw_bar_length_mm risiede sul materiale grezzo, non sul finito (TASK-V2-126)
    raw_material_code = (sync_art.materiale_grezzo_codice or "").strip() if sync_art else ""
    raw_bar_length_mm = None
    if raw_material_code:
        resolved_raw_code = _resolve_sync_articolo_code(session, raw_material_code) or raw_material_code
        raw_cfg = session.get(CoreArticoloConfig, resolved_raw_code)
        if raw_cfg is None:
            raw_cfg = session.scalar(
                select(CoreArticoloConfig).where(
                    func.upper(CoreArticoloConfig.codice_articolo) == resolved_raw_code.upper()
                )
            )
        raw_bar_length_mm = raw_cfg.raw_bar_length_mm if raw_cfg is not None else None

    # capacity_effective_qty da stock metrics (lazy import per evitare circular)
    from nssp_v2.core.stock_policy import list_stock_metrics_v1  # noqa: PLC0415
    all_metrics = list_stock_metrics_v1(session)
    stock_metric = next(
        (m for m in all_metrics if m.article_code == resolved_code.strip().upper()),
        None,
    )
    capacity_effective_qty = stock_metric.capacity_effective_qty if stock_metric else None

    _bar_fn = (
        compute_full_bar_qty_v2_capacity_floor
        if logic_key == "proposal_full_bar_v2_capacity_floor"
        else compute_full_bar_qty
    )
    result = _bar_fn(
        required_qty_total=required_qty_total,
        customer_shortage_qty=item.customer_shortage_qty,
        availability_qty=item.availability_qty,
        capacity_effective_qty=capacity_effective_qty,
        raw_bar_length_mm=raw_bar_length_mm,
        occorrente=occorrente,
        scarto=scarto,
    )

    if result.used_fallback:
        return result.proposed_qty, params_snapshot, True, result.fallback_reason

    updated_snapshot = {**params_snapshot, "_bars_required": result.bars_required}
    return result.proposed_qty, updated_snapshot, False, None


def _workspace_row_from_candidate(
    session: Session,
    item: PlanningCandidateItem,
    now: datetime,
    workspace_id: str,
) -> CoreProposalWorkspaceRow:
    resolved_code = _resolve_sync_articolo_code(session, item.article_code) or item.article_code
    global_cfg = get_proposal_logic_config(session)
    article_logic_key, article_params = _resolve_article_proposal_config(session, item.article_code)
    requested_logic_key = article_logic_key or global_cfg.default_logic_key
    logic_key = requested_logic_key
    global_params = dict(global_cfg.logic_params_by_key.get(requested_logic_key, {}))
    params_snapshot = merge_logic_params(global_params, article_params)
    required_qty_total = _canonical_required_qty_total(item)

    fallback_reason: str | None = None
    if requested_logic_key in ("proposal_full_bar_v1", "proposal_full_bar_v2_capacity_floor"):
        proposed_qty, params_snapshot, used_fallback, fallback_reason = _resolve_full_bar_proposed_qty(
            session, item, required_qty_total, params_snapshot, logic_key=requested_logic_key
        )
        if used_fallback:
            logic_key = "proposal_target_pieces_v1"
    else:
        proposed_qty = compute_proposed_qty(logic_key, required_qty_total, params_snapshot)

    effective_logic_key = logic_key

    return CoreProposalWorkspaceRow(
        workspace_id=workspace_id,
        source_candidate_id=item.source_candidate_id,
        planning_mode=item.planning_mode,
        article_code=resolved_code,
        display_label=item.display_label,
        display_description=item.display_description,
        description_parts_json=list(item.description_parts),
        primary_driver=item.primary_driver,
        required_qty_minimum=item.required_qty_minimum,
        required_qty_total=required_qty_total,
        customer_shortage_qty=item.customer_shortage_qty,
        stock_replenishment_qty=item.stock_replenishment_qty,
        requested_delivery_date=(
            item.requested_delivery_date
            if item.planning_mode == "by_customer_order_line"
            else item.earliest_customer_delivery_date
        ),
        requested_destination_display=item.requested_destination_display,
        active_warning_codes_json=list(item.active_warning_codes),
        proposal_logic_key=logic_key,
        proposal_logic_params_snapshot_json=dict(params_snapshot),
        proposed_qty=proposed_qty,
        override_qty=None,
        override_reason=None,
        final_qty=proposed_qty,
        order_reference=item.order_reference,
        line_reference=item.line_reference,
        computed_at=item.computed_at.replace(tzinfo=timezone.utc) if item.computed_at.tzinfo is None else item.computed_at,
        created_at=now,
        updated_at=now,
        # Diagnostica logica proposal (TASK-V2-124)
        requested_proposal_logic_key=requested_logic_key,
        effective_proposal_logic_key=effective_logic_key,
        proposal_fallback_reason=fallback_reason,
    )


def _workspace_to_detail(session: Session, workspace: CoreProposalWorkspace) -> ProposalWorkspaceDetail:
    rows = session.scalars(
        select(CoreProposalWorkspaceRow)
        .where(CoreProposalWorkspaceRow.workspace_id == workspace.workspace_id)
        .order_by(CoreProposalWorkspaceRow.row_id.asc())
    ).all()
    article_codes = {row.article_code.strip().upper() for row in rows}
    preview_map = _load_articolo_preview_data(session, article_codes)
    return ProposalWorkspaceDetail(
        workspace_id=workspace.workspace_id,
        status=workspace.status,  # type: ignore[arg-type]
        created_at=workspace.created_at,
        expires_at=workspace.expires_at,
        updated_at=workspace.updated_at,
        rows=[
            _workspace_row_to_item(row, preview_map)
            for row in rows
        ],
    )


def _workspace_row_to_item(
    row: CoreProposalWorkspaceRow,
    preview_map: dict[str, _ArticoloPreview],
) -> ProposalWorkspaceRowItem:
    parts = list(row.description_parts_json or [])
    preview = preview_map.get(row.article_code.strip().upper())
    return ProposalWorkspaceRowItem(
        row_id=row.row_id,
        source_candidate_id=row.source_candidate_id,
        planning_mode=row.planning_mode,
        article_code=row.article_code,
        display_label=row.display_label,
        display_description=row.display_description,
        primary_driver=row.primary_driver,  # type: ignore[arg-type]
        required_qty_minimum=row.required_qty_minimum,
        required_qty_total=row.required_qty_total,
        customer_shortage_qty=row.customer_shortage_qty,
        stock_replenishment_qty=row.stock_replenishment_qty,
        requested_delivery_date=row.requested_delivery_date,
        requested_destination_display=row.requested_destination_display,
        active_warning_codes=list(row.active_warning_codes_json or []),
        proposal_logic_key=row.proposal_logic_key,
        proposed_qty=row.proposed_qty,
        override_qty=row.override_qty,
        override_reason=row.override_reason,
        final_qty=row.final_qty,
        order_reference=row.order_reference,
        line_reference=row.line_reference,
        computed_at=row.computed_at,
        updated_at=row.updated_at,
        # export-preview (TASK-V2-115)
        description_parts=parts,
        export_description=_export_description(parts),
        codice_immagine=preview.codice_immagine if preview else None,
        materiale=preview.materiale if preview else None,
        mm_materiale=preview.mm_materiale if preview else None,
        ordine=_ordine_from_row(row.primary_driver, row.planning_mode, row.order_reference),
        ordine_linea_mancante=_ordine_linea_mancante(row.primary_driver, row.planning_mode, row.line_reference),
        note_preview=_workspace_note_preview(
            row.requested_delivery_date,
            row.proposal_logic_key,
            dict(row.proposal_logic_params_snapshot_json or {}),
        ),
        user_preview=_USER_PREVIEW,
        # Diagnostica logica proposal (TASK-V2-124)
        requested_proposal_logic_key=row.requested_proposal_logic_key,
        effective_proposal_logic_key=row.effective_proposal_logic_key,
        proposal_fallback_reason=row.proposal_fallback_reason,
    )


def _proposal_to_item(
    row: CoreProductionProposal,
    preview: _ArticoloPreview | None = None,
) -> ProductionProposalItem:
    parts = list(row.description_parts_json or [])
    return ProductionProposalItem(
        proposal_id=row.proposal_id,
        source_candidate_id=row.source_candidate_id,
        workspace_id=row.workspace_id,
        workspace_row_id=row.workspace_row_id,
        planning_mode=row.planning_mode,
        article_code=row.article_code,
        display_label=row.display_label,
        display_description=row.display_description,
        primary_driver=row.primary_driver,  # type: ignore[arg-type]
        required_qty_minimum=row.required_qty_minimum,
        required_qty_total=row.required_qty_total,
        customer_shortage_qty=row.customer_shortage_qty,
        stock_replenishment_qty=row.stock_replenishment_qty,
        requested_delivery_date=row.requested_delivery_date,
        requested_destination_display=row.requested_destination_display,
        active_warning_codes=list(row.active_warning_codes_json or []),
        proposal_logic_key=row.proposal_logic_key,
        proposed_qty=row.proposed_qty,
        override_qty=row.override_qty,
        override_reason=row.override_reason,
        final_qty=row.final_qty,
        workflow_status=row.workflow_status,  # type: ignore[arg-type]
        ode_ref=row.ode_ref,
        export_batch_id=row.export_batch_id,
        reconciled_production_bucket=row.reconciled_production_bucket,
        reconciled_production_id_dettaglio=row.reconciled_production_id_dettaglio,
        order_reference=row.order_reference,
        line_reference=row.line_reference,
        computed_at=row.computed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        # export-preview (TASK-V2-115)
        description_parts=parts,
        export_description=_export_description(parts),
        codice_immagine=preview.codice_immagine if preview else None,
        materiale=preview.materiale if preview else None,
        mm_materiale=preview.mm_materiale if preview else None,
        ordine=_ordine_from_row(row.primary_driver, row.planning_mode, row.order_reference),
        ordine_linea_mancante=_ordine_linea_mancante(row.primary_driver, row.planning_mode, row.line_reference),
        note_preview=row.ode_ref,
        user_preview=_USER_PREVIEW,
    )


def _abandon_expired_workspaces(session: Session, now: datetime) -> int:
    rows = session.scalars(
        select(CoreProposalWorkspace)
        .where(CoreProposalWorkspace.status == "open")
        .where(CoreProposalWorkspace.expires_at < now)
    ).all()
    for row in rows:
        row.status = "abandoned"
        row.updated_at = now
    if rows:
        session.flush()
    return len(rows)


def generate_proposal_workspace(
    session: Session,
    source_candidate_ids: list[str],
    customer_horizon_days: int = 30,
    user_areas: list[str] | None = None,
    is_admin: bool = False,
) -> ProposalWorkspaceGenerateResult:
    selected_ids = list(dict.fromkeys(source_candidate_ids))
    if not selected_ids:
        raise ValueError("Nessun candidate selezionato")

    now = datetime.now(timezone.utc)
    _abandon_expired_workspaces(session, now)

    candidates = list_planning_candidates_v1(
        session,
        customer_horizon_days=customer_horizon_days,
        user_areas=user_areas or ["produzione"],
        is_admin=is_admin,
    )
    candidate_by_id = {item.source_candidate_id: item for item in candidates}
    selected_items = [candidate_by_id[cid] for cid in selected_ids if cid in candidate_by_id]
    skipped_missing = len(selected_ids) - len(selected_items)
    if not selected_items:
        raise ValueError("I candidate selezionati non sono piu disponibili")

    workspace_id = str(uuid.uuid4())
    workspace = CoreProposalWorkspace(
        workspace_id=workspace_id,
        status="open",
        export_batch_id=None,
        created_at=now,
        expires_at=now + timedelta(hours=_WORKSPACE_TTL_HOURS),
        updated_at=now,
    )
    session.add(workspace)
    session.flush()

    for item in selected_items:
        session.add(_workspace_row_from_candidate(session, item, now, workspace_id))

    session.commit()
    return ProposalWorkspaceGenerateResult(
        workspace_id=workspace_id,
        created_count=len(selected_items),
        skipped_missing_count=skipped_missing,
        workspace_row_count=len(selected_items),
    )


def get_proposal_workspace_detail(session: Session, workspace_id: str) -> ProposalWorkspaceDetail | None:
    now = datetime.now(timezone.utc)
    _abandon_expired_workspaces(session, now)
    session.commit()
    workspace = session.get(CoreProposalWorkspace, workspace_id)
    if workspace is None:
        return None
    return _workspace_to_detail(session, workspace)


def set_proposal_workspace_row_override(
    session: Session,
    workspace_id: str,
    row_id: int,
    override_qty: Decimal | None,
    override_reason: str | None,
) -> ProposalWorkspaceDetail:
    now = datetime.now(timezone.utc)
    _abandon_expired_workspaces(session, now)
    workspace = session.get(CoreProposalWorkspace, workspace_id)
    if workspace is None:
        raise ValueError("Workspace non trovato")
    if workspace.status != "open":
        raise ValueError("Workspace non modificabile nello stato corrente")
    row = session.get(CoreProposalWorkspaceRow, row_id)
    if row is None or row.workspace_id != workspace_id:
        raise ValueError("Workspace row non trovata")
    row.override_qty = override_qty
    row.override_reason = override_reason.strip() if override_reason else None
    row.final_qty = resolve_final_qty(row.proposed_qty, row.override_qty)
    row.updated_at = now
    workspace.updated_at = now
    session.commit()
    return _workspace_to_detail(session, workspace)


def abandon_proposal_workspace(session: Session, workspace_id: str) -> None:
    workspace = session.get(CoreProposalWorkspace, workspace_id)
    if workspace is None:
        raise ValueError("Workspace non trovato")
    if workspace.status == "exported":
        raise ValueError("Workspace gia esportato")
    workspace.status = "abandoned"
    workspace.updated_at = datetime.now(timezone.utc)
    session.commit()


def export_proposal_workspace_csv(
    session: Session,
    workspace_id: str,
) -> tuple[ProductionProposalExportBatchResult, str]:
    now = datetime.now(timezone.utc)
    _abandon_expired_workspaces(session, now)
    workspace = session.get(CoreProposalWorkspace, workspace_id)
    if workspace is None:
        raise ValueError("Workspace non trovato")
    if workspace.status != "open":
        raise ValueError("Workspace non esportabile nello stato corrente")

    rows = session.scalars(
        select(CoreProposalWorkspaceRow)
        .where(CoreProposalWorkspaceRow.workspace_id == workspace_id)
        .order_by(CoreProposalWorkspaceRow.row_id.asc())
    ).all()
    if not rows:
        raise ValueError("Workspace vuoto")

    batch_id = str(uuid.uuid4())
    batch = CoreProductionProposalExportBatch(
        batch_id=batch_id,
        proposal_count=len(rows),
        created_at=now,
    )
    session.add(batch)
    session.flush()

    exported_rows: list[CoreProductionProposal] = []
    for row in rows:
        exported = CoreProductionProposal(
            source_candidate_id=row.source_candidate_id,
            workspace_id=workspace.workspace_id,
            workspace_row_id=row.row_id,
            planning_mode=row.planning_mode,
            article_code=row.article_code,
            display_label=row.display_label,
            display_description=row.display_description,
            description_parts_json=list(row.description_parts_json or []),
            primary_driver=row.primary_driver,
            required_qty_minimum=row.required_qty_minimum,
            required_qty_total=row.required_qty_total,
            customer_shortage_qty=row.customer_shortage_qty,
            stock_replenishment_qty=row.stock_replenishment_qty,
            requested_delivery_date=row.requested_delivery_date,
            requested_destination_display=row.requested_destination_display,
            active_warning_codes_json=list(row.active_warning_codes_json or []),
            proposal_logic_key=row.proposal_logic_key,
            proposal_logic_params_snapshot_json=dict(row.proposal_logic_params_snapshot_json or {}),
            proposed_qty=row.proposed_qty,
            override_qty=row.override_qty,
            override_reason=row.override_reason,
            final_qty=row.final_qty,
            workflow_status="exported",
            ode_ref="PENDING",
            export_batch_id=batch_id,
            reconciled_production_bucket=None,
            reconciled_production_id_dettaglio=None,
            order_reference=row.order_reference,
            line_reference=row.line_reference,
            computed_at=row.computed_at,
            created_at=now,
            updated_at=now,
        )
        session.add(exported)
        exported_rows.append(exported)
    session.flush()

    for exported in exported_rows:
        exported.ode_ref = f"ODE_REF:PROP:{exported.proposal_id}"

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "proposal_id",
            "ode_ref",
            "note_articolo",
            "article_code",
            "display_description",
            "planning_mode",
            "required_qty_total",
            "proposed_qty",
            "override_qty",
            "final_qty",
            "primary_driver",
            "requested_delivery_date",
            "requested_destination_display",
            "order_reference",
            "line_reference",
            "active_warning_codes",
        ],
    )
    writer.writeheader()
    for exported in exported_rows:
        writer.writerow(
            {
                "proposal_id": exported.proposal_id,
                "ode_ref": exported.ode_ref,
                "note_articolo": exported.ode_ref,
                "article_code": exported.article_code,
                "display_description": exported.display_description,
                "planning_mode": exported.planning_mode or "",
                "required_qty_total": str(exported.required_qty_total),
                "proposed_qty": str(exported.proposed_qty),
                "override_qty": "" if exported.override_qty is None else str(exported.override_qty),
                "final_qty": str(exported.final_qty),
                "primary_driver": exported.primary_driver or "",
                "requested_delivery_date": exported.requested_delivery_date.isoformat() if exported.requested_delivery_date else "",
                "requested_destination_display": exported.requested_destination_display or "",
                "order_reference": exported.order_reference or "",
                "line_reference": "" if exported.line_reference is None else str(exported.line_reference),
                "active_warning_codes": ",".join(exported.active_warning_codes_json or []),
            }
        )

    workspace.status = "exported"
    workspace.export_batch_id = batch_id
    workspace.updated_at = now
    session.commit()

    return (
        ProductionProposalExportBatchResult(
            batch_id=batch_id,
            filename=f"production-proposals-{batch_id}.csv",
            exported_count=len(exported_rows),
            exported_at=now,
            workspace_id=workspace_id,
        ),
        buffer.getvalue(),
    )


def list_production_proposals(
    session: Session,
    workflow_status: str | None = None,
    proposal_ids: list[int] | None = None,
) -> list[ProductionProposalItem]:
    query = select(CoreProductionProposal).order_by(
        CoreProductionProposal.created_at.desc(),
        CoreProductionProposal.proposal_id.desc(),
    )
    if workflow_status:
        query = query.where(CoreProductionProposal.workflow_status == workflow_status)
    if proposal_ids:
        query = query.where(CoreProductionProposal.proposal_id.in_(proposal_ids))
    rows = session.scalars(query).all()
    article_codes = {row.article_code.strip().upper() for row in rows}
    preview_map = _load_articolo_preview_data(session, article_codes)
    return [_proposal_to_item(row, preview_map.get(row.article_code.strip().upper())) for row in rows]


def get_production_proposal_detail(session: Session, proposal_id: int) -> ProductionProposalDetail | None:
    row = session.get(CoreProductionProposal, proposal_id)
    if row is None:
        return None
    preview_map = _load_articolo_preview_data(session, {row.article_code.strip().upper()})
    preview = preview_map.get(row.article_code.strip().upper())
    return ProductionProposalDetail(
        **_proposal_to_item(row, preview).model_dump(),
        proposal_logic_params_snapshot=dict(row.proposal_logic_params_snapshot_json or {}),
    )


def reconcile_production_proposals(
    session: Session,
    proposal_ids: list[int] | None = None,
) -> ProductionProposalReconcileResult:
    query = select(CoreProductionProposal).where(CoreProductionProposal.workflow_status == "exported")
    if proposal_ids:
        query = query.where(CoreProductionProposal.proposal_id.in_(proposal_ids))
    rows = session.scalars(query).all()
    active = session.scalars(select(SyncProduzioneAttiva)).all()
    historical = session.scalars(select(SyncProduzioneStorica)).all()

    matched = 0
    unmatched = 0
    now = datetime.now(timezone.utc)

    for row in rows:
        hit = next(
            (
                ("active", prod.id_dettaglio)
                for prod in active
                if prod.note_articolo and row.ode_ref in prod.note_articolo
            ),
            None,
        )
        if hit is None:
            hit = next(
                (
                    ("historical", prod.id_dettaglio)
                    for prod in historical
                    if prod.note_articolo and row.ode_ref in prod.note_articolo
                ),
                None,
            )
        if hit is None:
            unmatched += 1
            continue
        row.workflow_status = "reconciled"
        row.reconciled_production_bucket = hit[0]
        row.reconciled_production_id_dettaglio = hit[1]
        row.updated_at = now
        matched += 1

    session.commit()
    return ProductionProposalReconcileResult(
        matched=matched,
        unmatched=unmatched,
        scanned=len(rows),
        reconciled_at=now,
    )
