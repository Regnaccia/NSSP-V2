"""ORM models for proposal workspaces and exported proposal history."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreProposalLogicConfig(Base):
    """Singleton global config for proposal logic registry."""

    __tablename__ = "core_proposal_logic_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    default_logic_key: Mapped[str] = mapped_column(String(64), nullable=False)
    logic_params_by_key_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Liste di logic key esplicitamente disabilitate (TASK-V2-130).
    # Una logica in questa lista resta nel registro ma non e assegnabile agli articoli.
    disabled_logic_keys_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CoreProposalWorkspace(Base):
    """Temporary proposal workspace generated from selected planning candidates."""

    __tablename__ = "core_proposal_workspaces"

    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    export_batch_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("core_production_proposal_export_batches.batch_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CoreProposalWorkspaceRow(Base):
    """Frozen candidate snapshot inside a temporary proposal workspace."""

    __tablename__ = "core_proposal_workspace_rows"

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("core_proposal_workspaces.workspace_id"),
        nullable=False,
        index=True,
    )
    source_candidate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    planning_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    article_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    display_label: Mapped[str] = mapped_column(String(255), nullable=False)
    display_description: Mapped[str] = mapped_column(Text, nullable=False)
    primary_driver: Mapped[str | None] = mapped_column(String(32), nullable=True)
    required_qty_minimum: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    required_qty_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    customer_shortage_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    stock_replenishment_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    requested_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    requested_destination_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_parts_json: Mapped[list] = mapped_column(JSON, nullable=False)
    active_warning_codes_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    proposal_logic_key: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_logic_params_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    proposed_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    override_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    order_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    line_reference: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Diagnostica logica proposal (TASK-V2-124)
    requested_proposal_logic_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_proposal_logic_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proposal_fallback_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CoreProductionProposalExportBatch(Base):
    """Minimal audit entity for CSV export batches."""

    __tablename__ = "core_production_proposal_export_batches"

    batch_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    proposal_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CoreProductionProposal(Base):
    """Persistent exported proposal snapshot plus reconcile status."""

    __tablename__ = "core_production_proposals"

    proposal_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_candidate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("core_proposal_workspaces.workspace_id"),
        nullable=True,
        index=True,
    )
    workspace_row_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("core_proposal_workspace_rows.row_id"),
        nullable=True,
        index=True,
    )
    planning_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    article_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    display_label: Mapped[str] = mapped_column(String(255), nullable=False)
    display_description: Mapped[str] = mapped_column(Text, nullable=False)
    primary_driver: Mapped[str | None] = mapped_column(String(32), nullable=True)
    required_qty_minimum: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    required_qty_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    customer_shortage_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    stock_replenishment_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    requested_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    requested_destination_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_parts_json: Mapped[list] = mapped_column(JSON, nullable=False)
    active_warning_codes_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    proposal_logic_key: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_logic_params_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    proposed_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    override_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    workflow_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    ode_ref: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    export_batch_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("core_production_proposal_export_batches.batch_id"),
        nullable=True,
    )
    reconciled_production_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reconciled_production_id_dettaglio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    line_reference: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
