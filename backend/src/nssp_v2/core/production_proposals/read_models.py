"""Read models for proposal workspaces and exported proposal history.

Campi export-preview (TASK-V2-115):
  description_parts      — parti descrittive canoniche (lista ordinata)
  export_description     — serializzazione Python-list-repr per colonna EasyJob
  codice_immagine        — COD_IMM da sync_articoli
  materiale              — MAT_COD da sync_articoli
  mm_materiale           — REGN_QT_OCCORR da sync_articoli
  ordine                 — order_reference per driver customer; None per stock-only
  ordine_linea_mancante  — True se driver customer ma line_reference assente (errore semantico)
  note_preview           — valore che andra in NOTE_ARTICOLO su EasyJob (ode_ref per esportati,
                           stringa vuota per workspace non ancora esportato)
  user_preview           — utente EasyJob placeholder (V1: 'NSSP')
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExportedProposalWorkflowStatus = Literal["exported", "reconciled", "cancelled"]
ProposalWorkspaceStatus = Literal["open", "exported", "abandoned"]


class ProposalWorkspaceRowItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    row_id: int
    source_candidate_id: str
    planning_mode: str | None
    article_code: str
    display_label: str
    display_description: str
    primary_driver: Literal["customer", "stock"] | None = None
    required_qty_minimum: Decimal
    required_qty_total: Decimal
    customer_shortage_qty: Decimal | None = None
    stock_replenishment_qty: Decimal | None = None
    requested_delivery_date: date | None = None
    requested_destination_display: str | None = None
    active_warning_codes: list[str] = Field(default_factory=list)
    proposal_logic_key: str
    proposed_qty: Decimal
    override_qty: Decimal | None = None
    override_reason: str | None = None
    final_qty: Decimal
    order_reference: str | None = None
    line_reference: int | None = None
    computed_at: datetime
    updated_at: datetime

    # ─── Campi export-preview (TASK-V2-115) ──────────────────────────────────
    description_parts: list[str] = Field(default_factory=list)
    export_description: str = ""
    codice_immagine: str | None = None
    materiale: str | None = None
    mm_materiale: Decimal | None = None
    ordine: str | None = None
    ordine_linea_mancante: bool = False
    note_preview: str = ""
    user_preview: str = "NSSP"


class ProposalWorkspaceDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: str
    status: ProposalWorkspaceStatus
    created_at: datetime
    expires_at: datetime
    updated_at: datetime
    rows: list[ProposalWorkspaceRowItem]


class ProposalWorkspaceGenerateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: str
    created_count: int
    skipped_missing_count: int
    workspace_row_count: int


class ProductionProposalItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: int
    source_candidate_id: str
    workspace_id: str | None = None
    workspace_row_id: int | None = None
    planning_mode: str | None
    article_code: str
    display_label: str
    display_description: str
    primary_driver: Literal["customer", "stock"] | None = None
    required_qty_minimum: Decimal
    required_qty_total: Decimal
    customer_shortage_qty: Decimal | None = None
    stock_replenishment_qty: Decimal | None = None
    requested_delivery_date: date | None = None
    requested_destination_display: str | None = None
    active_warning_codes: list[str] = Field(default_factory=list)
    proposal_logic_key: str
    proposed_qty: Decimal
    override_qty: Decimal | None = None
    override_reason: str | None = None
    final_qty: Decimal
    workflow_status: ExportedProposalWorkflowStatus
    ode_ref: str
    export_batch_id: str | None = None
    reconciled_production_bucket: str | None = None
    reconciled_production_id_dettaglio: int | None = None
    order_reference: str | None = None
    line_reference: int | None = None
    computed_at: datetime
    created_at: datetime
    updated_at: datetime

    # ─── Campi export-preview (TASK-V2-115) ──────────────────────────────────
    description_parts: list[str] = Field(default_factory=list)
    export_description: str = ""
    codice_immagine: str | None = None
    materiale: str | None = None
    mm_materiale: Decimal | None = None
    ordine: str | None = None
    ordine_linea_mancante: bool = False
    note_preview: str = ""
    user_preview: str = "NSSP"


class ProductionProposalDetail(ProductionProposalItem):
    proposal_logic_params_snapshot: dict


class ProductionProposalReconcileResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    matched: int
    unmatched: int
    scanned: int
    reconciled_at: datetime


class ProductionProposalExportBatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    batch_id: str
    filename: str
    exported_count: int
    exported_at: datetime
    workspace_id: str
