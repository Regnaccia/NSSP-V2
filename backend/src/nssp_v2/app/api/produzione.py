"""
Router surface produzione — Core slice articoli + produzioni + warnings (TASK-V2-020,
TASK-V2-022, TASK-V2-030, TASK-V2-078).

Endpoint:
  GET   /api/produzione/articoli                                  — lista articoli attivi
  GET   /api/produzione/articoli/{codice}                         — dettaglio articolo
  GET   /api/produzione/famiglie                                  — catalogo famiglie
  PATCH /api/produzione/articoli/{codice}/famiglia                — imposta famiglia articolo
  GET   /api/produzione/produzioni                                — lista produzioni (attive + storiche)
  PATCH /api/produzione/produzioni/{id_dettaglio}/forza-completata — override flag forza_completata
  GET   /api/produzione/warnings                                  — tutti i warning canonici (surface Warnings e punto trasversale)

Tutti gli endpoint richiedono autenticazione Bearer.
Il Core non espone mai i target sync_* grezzi.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.core.criticita import CriticitaItem, list_criticita_v1
from nssp_v2.core.planning_candidates import PlanningCandidateItem, list_planning_candidates_v1
from nssp_v2.core.production_proposals import (
    KNOWN_PROPOSAL_LOGICS,
    ProductionProposalDetail,
    ProductionProposalItem,
    ProductionProposalReconcileResult,
    ProposalWorkspaceDetail,
    ProposalWorkspaceGenerateResult,
    abandon_proposal_workspace,
    export_proposal_workspace_csv,
    generate_proposal_workspace,
    get_production_proposal_detail,
    get_proposal_workspace_detail,
    list_production_proposals,
    reconcile_production_proposals,
    set_proposal_workspace_row_override,
)
from nssp_v2.core.warnings import WarningItem, list_warnings_v1, filter_warnings_by_areas
from nssp_v2.core.warnings.config import KNOWN_AREAS
from nssp_v2.core.produzioni import ProduzioneItem, ProduzioniPaginata, list_produzioni, set_forza_completata
from nssp_v2.core.articoli import (
    ArticoloDetail,
    ArticoloItem,
    FamigliaItem,
    FamigliaRow,
    create_famiglia,
    get_articolo_detail,
    list_articoli,
    list_famiglie,
    list_famiglie_catalog,
    set_articolo_gestione_scorte_override,
    set_articolo_policy_override,
    set_articolo_proposal_logic_config,
    set_articolo_raw_bar_length_mm,
    set_articolo_stock_policy_override,
    set_famiglia_articolo,
    set_famiglia_stock_policy,
    toggle_famiglia_active,
    toggle_famiglia_aggrega_codice_produzione,
    toggle_famiglia_considera_produzione,
    toggle_famiglia_gestione_scorte,
    toggle_famiglia_raw_bar_length_mm_enabled,
)
from nssp_v2.shared.db import get_session

router = APIRouter(prefix="/produzione", tags=["produzione"])


class SetForzaCompletataRequest(BaseModel):
    bucket: str
    forza_completata: bool


class SetFamigliaRequest(BaseModel):
    famiglia_code: str | None = None


class SetPolicyOverrideRequest(BaseModel):
    """Corpo PATCH policy-override articolo (DL-ARCH-V2-026, TASK-V2-067).

    Entrambi i campi sono applicati al momento della chiamata.
    - None  = eredita il default di famiglia (rimuove l'override)
    - True  = sovrascrive con True
    - False = sovrascrive con False
    """
    override_considera_in_produzione: bool | None
    override_aggrega_codice_in_produzione: bool | None


class CreateFamigliaRequest(BaseModel):
    code: str
    label: str
    sort_order: int | None = None


class SetFamigliaStockPolicyRequest(BaseModel):
    """Corpo PATCH stock-policy famiglia (DL-ARCH-V2-030, TASK-V2-093).

    stock_months e stock_trigger_months sono nullable: None rimuove il default.
    Validi solo per articoli con planning_mode = by_article (aggrega_codice_in_produzione = True).
    """
    stock_months: float | None
    stock_trigger_months: float | None


class SetStockPolicyOverrideRequest(BaseModel):
    """Corpo PATCH stock-policy-override articolo (DL-ARCH-V2-030, TASK-V2-089).

    Tutti i campi sono opzionali nel body ma vengono sempre applicati al momento della chiamata.
    - None  = eredita il default di famiglia (rimuove l'override)
    - valore numerico = sovrascrive
    """
    override_stock_months: float | None
    override_stock_trigger_months: float | None
    capacity_override_qty: float | None


class SetGestioneScorteOverrideRequest(BaseModel):
    """Corpo PATCH gestione-scorte-override articolo (TASK-V2-098).

    - None  = eredita il default di famiglia (rimuove l'override)
    - True  = sovrascrive con True
    - False = sovrascrive con False
    """
    override_gestione_scorte_attiva: bool | None


class SetRawBarLengthMmRequest(BaseModel):
    """Corpo PATCH raw-bar-length-mm articolo (TASK-V2-118).

    - None = rimuove il valore (nessun default famiglia)
    - valore numerico = imposta la lunghezza barra in mm
    """
    raw_bar_length_mm: float | None


class SetProposalLogicArticleConfigRequest(BaseModel):
    proposal_logic_key: str | None
    proposal_logic_article_params: dict | None = None


class GenerateProposalWorkspaceRequest(BaseModel):
    source_candidate_ids: list[str]


class SetProposalWorkspaceRowOverrideRequest(BaseModel):
    override_qty: float | None
    override_reason: str | None = None


class ReconcileProductionProposalsRequest(BaseModel):
    proposal_ids: list[int] | None = None


class ProposalLogicCatalogResponse(BaseModel):
    known_logics: list[str]
    default_logic_key: str


@router.get("/articoli", response_model=list[ArticoloItem])
def get_articoli(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista articoli attivi con famiglia interna, ordinata per codice_articolo."""
    return list_articoli(session)


@router.get("/articoli/{codice_articolo:path}", response_model=ArticoloDetail)
def get_articolo(
    codice_articolo: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Dettaglio completo dell'articolo con famiglia interna. 404 se non trovato."""
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articolo '{codice_articolo}' non trovato",
        )
    return detail


@router.get("/famiglie/catalog", response_model=list[FamigliaRow])
def get_famiglie_catalog(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Tabella completa famiglie (attive e inattive) con conteggio articoli assegnati."""
    return list_famiglie_catalog(session)


@router.post("/famiglie", response_model=FamigliaRow, status_code=status.HTTP_201_CREATED)
def post_famiglia(
    body: CreateFamigliaRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Crea una nuova famiglia articolo. 422 se code duplicato o label vuota."""
    try:
        row = create_famiglia(session, body.code, body.label, body.sort_order)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch("/famiglie/{code}/active", response_model=FamigliaRow)
def patch_famiglia_active(
    code: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Inverte is_active della famiglia. 404 se non trovata."""
    try:
        row = toggle_famiglia_active(session, code)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/famiglie/{code}/aggrega-codice-produzione", response_model=FamigliaRow)
def patch_famiglia_aggrega_codice_produzione(
    code: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Inverte aggrega_codice_in_produzione della famiglia. 404 se non trovata."""
    try:
        row = toggle_famiglia_aggrega_codice_produzione(session, code)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/famiglie/{code}/considera-produzione", response_model=FamigliaRow)
def patch_famiglia_considera_produzione(
    code: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Inverte considera_in_produzione della famiglia. 404 se non trovata."""
    try:
        row = toggle_famiglia_considera_produzione(session, code)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/famiglie/{code}/stock-policy", response_model=FamigliaRow)
def patch_famiglia_stock_policy(
    code: str,
    body: SetFamigliaStockPolicyRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta i default stock policy della famiglia V1 (TASK-V2-093).

    body.stock_months: null = rimuove il default, valore = imposta.
    body.stock_trigger_months: null = rimuove il default, valore = imposta.
    404 se la famiglia non esiste.
    """
    from decimal import Decimal
    try:
        row = set_famiglia_stock_policy(
            session,
            code,
            stock_months=Decimal(str(body.stock_months)) if body.stock_months is not None else None,
            stock_trigger_months=Decimal(str(body.stock_trigger_months)) if body.stock_trigger_months is not None else None,
        )
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/famiglie/{code}/gestione-scorte", response_model=FamigliaRow)
def patch_famiglia_gestione_scorte(
    code: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Inverte il flag gestione_scorte_attiva della famiglia (TASK-V2-096, TASK-V2-097).

    Prerequisito per la stock policy: planning_mode = by_article.
    404 se la famiglia non esiste.
    """
    try:
        row = toggle_famiglia_gestione_scorte(session, code)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/famiglie/{code}/raw-bar-length-enabled", response_model=FamigliaRow)
def patch_famiglia_raw_bar_length_enabled(
    code: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Inverte il flag raw_bar_length_mm_enabled della famiglia (TASK-V2-118).

    Abilita o disabilita la configurabilita del dato lunghezza barra per gli articoli.
    404 se la famiglia non esiste.
    """
    try:
        row = toggle_famiglia_raw_bar_length_mm_enabled(session, code)
        session.commit()
        return row
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/famiglie", response_model=list[FamigliaItem])
def get_famiglie(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Catalogo famiglie articolo attive, ordinate per sort_order."""
    return list_famiglie(session)


@router.get("/produzioni", response_model=ProduzioniPaginata)
def get_produzioni(
    bucket: str = "active",
    limit: int = 50,
    offset: int = 0,
    stato: str | None = None,
    q: str | None = None,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista produzioni paginata con filtro bucket, stato e ricerca testuale.

    bucket: "active" (default) | "historical" | "all"
    limit:  max 200, default 50
    offset: default 0
    stato:  "attiva" | "completata" | (assente = tutti)
    q:      ricerca case-insensitive su codice_articolo e numero_documento
    """
    try:
        return list_produzioni(session, bucket=bucket, limit=limit, offset=offset, stato=stato, q=q)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch("/produzioni/{id_dettaglio}/forza-completata", response_model=ProduzioneItem)
def patch_forza_completata(
    id_dettaglio: int,
    body: SetForzaCompletataRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta il flag forza_completata per una produzione.

    body.bucket: "active" | "historical"
    body.forza_completata: true | false
    404 se id_dettaglio + bucket non trovati nel mirror.
    """
    try:
        item = set_forza_completata(session, id_dettaglio, body.bucket, body.forza_completata)
        session.commit()
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/criticita", response_model=list[CriticitaItem])
def get_criticita(
    solo_in_produzione: bool = True,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista articoli critici V1: availability_qty < 0, ordinati per disponibilita crescente.

    solo_in_produzione=true (default): solo articoli con famiglia.considera_in_produzione = true.
    solo_in_produzione=false: tutti gli articoli critici, utile per debug/popolamento famiglie.

    La logica di criticita e applicata nel Core (DL-ARCH-V2-023).
    """
    return list_criticita_v1(session, solo_in_produzione=solo_in_produzione)


@router.get("/planning-candidates", response_model=list[PlanningCandidateItem])
def get_planning_candidates(
    payload: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
    horizon_days: int = Query(default=30, ge=1, description="Orizzonte temporale in giorni usato solo per il filtro customer horizon (TASK-V2-104)."),
):
    """Lista planning candidates V1: future_availability_qty < 0, ordinati per fabbisogno minimo decrescente.

    Candidato = articolo scoperto anche dopo la supply gia in corso (produzioni attive).
    Regola V1: future_availability_qty = availability_qty + incoming_supply_qty < 0.

    Il parametro horizon_days controlla solo il flag is_within_customer_horizon.
    Il cap stock-driven usa esclusivamente effective_stock_months (stock horizon, TASK-V2-103).

    Il risultato include effective policy (DL-ARCH-V2-026) per consentire alla UI
    il filtro solo_in_produzione basato su effective_considera_in_produzione.

    La logica di candidatura e applicata nel Core (DL-ARCH-V2-023, DL-ARCH-V2-025).
    """
    roles: list[str] = payload.get("roles", [])
    is_admin = "admin" in roles
    user_areas = [r for r in roles if r in KNOWN_AREAS]
    return list_planning_candidates_v1(
        session,
        customer_horizon_days=horizon_days,
        user_areas=user_areas,
        is_admin=is_admin,
    )


@router.post("/planning-candidates/generate-proposals-workspace", response_model=ProposalWorkspaceGenerateResult)
def post_generate_proposals_workspace(
    body: GenerateProposalWorkspaceRequest,
    payload: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
    horizon_days: int = Query(default=30, ge=1, description="Orizzonte usato per leggere i candidate correnti prima del freeze."),
):
    roles: list[str] = payload.get("roles", [])
    is_admin = "admin" in roles
    user_areas = [r for r in roles if r in KNOWN_AREAS]
    try:
        return generate_proposal_workspace(
            session,
            source_candidate_ids=body.source_candidate_ids,
            customer_horizon_days=horizon_days,
            user_areas=user_areas,
            is_admin=is_admin,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch(
    "/articoli/{codice_articolo:path}/famiglia",
    status_code=status.HTTP_204_NO_CONTENT,
)
def patch_famiglia(
    codice_articolo: str,
    body: SetFamigliaRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta o rimuove la famiglia interna dell'articolo.

    Non modifica mai sync_articoli.
    famiglia_code=null rimuove l'associazione.
    """
    try:
        set_famiglia_articolo(session, codice_articolo, body.famiglia_code)
        session.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch(
    "/articoli/{codice_articolo:path}/policy-override",
    response_model=ArticoloDetail,
)
def patch_policy_override(
    codice_articolo: str,
    body: SetPolicyOverrideRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta gli override di planning policy per un articolo.

    body.override_considera_in_produzione: null = eredita famiglia, true/false = sovrascrive.
    body.override_aggrega_codice_in_produzione: null = eredita famiglia, true/false = sovrascrive.

    Restituisce il dettaglio aggiornato dell'articolo.
    404 se l'articolo non esiste in sync_articoli.
    """
    set_articolo_policy_override(
        session,
        codice_articolo,
        override_considera=body.override_considera_in_produzione,
        override_aggrega=body.override_aggrega_codice_in_produzione,
    )
    session.commit()
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articolo '{codice_articolo}' non trovato")
    return detail


@router.patch(
    "/articoli/{codice_articolo:path}/stock-policy-override",
    response_model=ArticoloDetail,
)
def patch_stock_policy_override(
    codice_articolo: str,
    body: SetStockPolicyOverrideRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta gli override di stock policy per un articolo (TASK-V2-089).

    body.override_stock_months: null = eredita famiglia, valore = sovrascrive.
    body.override_stock_trigger_months: null = eredita famiglia, valore = sovrascrive.
    body.capacity_override_qty: null = rimuove override, valore = sovrascrive.

    Restituisce il dettaglio aggiornato dell'articolo con metriche stock ricalcolate.
    404 se l'articolo non esiste in sync_articoli.
    """
    from decimal import Decimal
    set_articolo_stock_policy_override(
        session,
        codice_articolo,
        override_stock_months=Decimal(str(body.override_stock_months)) if body.override_stock_months is not None else None,
        override_stock_trigger_months=Decimal(str(body.override_stock_trigger_months)) if body.override_stock_trigger_months is not None else None,
        capacity_override_qty=Decimal(str(body.capacity_override_qty)) if body.capacity_override_qty is not None else None,
    )
    session.commit()
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articolo '{codice_articolo}' non trovato")
    return detail


@router.patch(
    "/articoli/{codice_articolo:path}/gestione-scorte-override",
    response_model=ArticoloDetail,
)
def patch_gestione_scorte_override(
    codice_articolo: str,
    body: SetGestioneScorteOverrideRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta l'override gestione_scorte_attiva per un articolo (TASK-V2-098).

    body.override_gestione_scorte_attiva: null = eredita famiglia, True/False = sovrascrive.

    Restituisce il dettaglio aggiornato dell'articolo.
    404 se l'articolo non esiste in sync_articoli.
    """
    set_articolo_gestione_scorte_override(
        session,
        codice_articolo,
        override_gestione_scorte_attiva=body.override_gestione_scorte_attiva,
    )
    session.commit()
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articolo '{codice_articolo}' non trovato")
    return detail


@router.patch(
    "/articoli/{codice_articolo:path}/proposal-logic",
    response_model=ArticoloDetail,
)
def patch_articolo_proposal_logic(
    codice_articolo: str,
    body: SetProposalLogicArticleConfigRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    set_articolo_proposal_logic_config(
        session,
        codice_articolo,
        proposal_logic_key=body.proposal_logic_key,
        proposal_logic_article_params=body.proposal_logic_article_params or {},
    )
    session.commit()
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articolo '{codice_articolo}' non trovato")
    return detail


@router.patch(
    "/articoli/{codice_articolo:path}/raw-bar-length-mm",
    response_model=ArticoloDetail,
)
def patch_articolo_raw_bar_length_mm(
    codice_articolo: str,
    body: SetRawBarLengthMmRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta o rimuove la lunghezza barra grezza per un articolo (TASK-V2-118).

    body.raw_bar_length_mm: null = rimuove il valore, valore = imposta in mm.

    Restituisce il dettaglio aggiornato dell'articolo.
    404 se l'articolo non esiste in sync_articoli.
    """
    from decimal import Decimal
    set_articolo_raw_bar_length_mm(
        session,
        codice_articolo,
        raw_bar_length_mm=Decimal(str(body.raw_bar_length_mm)) if body.raw_bar_length_mm is not None else None,
    )
    session.commit()
    detail = get_articolo_detail(session, codice_articolo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articolo '{codice_articolo}' non trovato")
    return detail


@router.get("/proposal-logic/catalog", response_model=ProposalLogicCatalogResponse)
def get_proposal_logic_catalog(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from nssp_v2.core.production_proposals import get_proposal_logic_config

    config = get_proposal_logic_config(session)
    return ProposalLogicCatalogResponse(
        known_logics=KNOWN_PROPOSAL_LOGICS,
        default_logic_key=config.default_logic_key,
    )


# ─── Warnings surface (TASK-V2-078, TASK-V2-081, TASK-V2-082) ────────────────

@router.get("/warnings", response_model=list[WarningItem])
def get_warnings(
    payload: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista warning visibili all'area/reparto dell'utente corrente (TASK-V2-082).

    Filtra i warning canonici sulle aree dell'utente, derivate dai ruoli JWT:
    - produzione / magazzino / logistica: vede solo i warning della propria area
    - admin: vede tutti i warning senza filtro

    La visibilita per area e governata da admin tramite visible_to_areas (TASK-V2-081).
    """
    roles: list[str] = payload.get("roles", [])
    is_admin = "admin" in roles
    user_areas = [r for r in roles if r in KNOWN_AREAS]
    all_warnings = list_warnings_v1(session)
    return filter_warnings_by_areas(all_warnings, user_areas, is_admin)


@router.get("/proposals", response_model=list[ProductionProposalItem])
def get_proposals(
    workflow_status: str | None = Query(default=None),
    proposal_ids: list[int] | None = Query(default=None),
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_production_proposals(session, workflow_status=workflow_status, proposal_ids=proposal_ids)


@router.get("/proposals/exported", response_model=list[ProductionProposalItem])
def get_exported_proposals(
    workflow_status: str | None = Query(default=None),
    proposal_ids: list[int] | None = Query(default=None),
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_production_proposals(session, workflow_status=workflow_status, proposal_ids=proposal_ids)


@router.get("/proposals/{proposal_id}", response_model=ProductionProposalDetail)
def get_proposal(
    proposal_id: int,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    detail = get_production_proposal_detail(session, proposal_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal esportata non trovata")
    return detail


@router.get("/proposals/exported/{proposal_id}", response_model=ProductionProposalDetail)
def get_exported_proposal(
    proposal_id: int,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    detail = get_production_proposal_detail(session, proposal_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal esportata non trovata")
    return detail


@router.get("/proposals/workspaces/{workspace_id}", response_model=ProposalWorkspaceDetail)
def get_proposal_workspace(
    workspace_id: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    detail = get_proposal_workspace_detail(session, workspace_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace non trovato")
    return detail


@router.patch("/proposals/workspaces/{workspace_id}/rows/{row_id}/override", response_model=ProposalWorkspaceDetail)
def patch_proposal_workspace_row_override(
    workspace_id: str,
    row_id: int,
    body: SetProposalWorkspaceRowOverrideRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        return set_proposal_workspace_row_override(
            session,
            workspace_id=workspace_id,
            row_id=row_id,
            override_qty=Decimal(str(body.override_qty)) if body.override_qty is not None else None,
            override_reason=body.override_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/proposals/workspaces/{workspace_id}/export")
def post_export_proposal_workspace(
    workspace_id: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        result, csv_text = export_proposal_workspace_csv(session, workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    headers = {
        "Content-Disposition": f'attachment; filename="{result.filename}"',
        "X-Export-Batch-Id": result.batch_id,
        "X-Exported-Count": str(result.exported_count),
        "X-Workspace-Id": result.workspace_id,
    }
    return StreamingResponse(iter([csv_text]), media_type="text/csv", headers=headers)


@router.post("/proposals/workspaces/{workspace_id}/abandon", status_code=status.HTTP_204_NO_CONTENT)
def post_abandon_proposal_workspace(
    workspace_id: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        abandon_proposal_workspace(session, workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/proposals/reconcile", response_model=ProductionProposalReconcileResult)
def post_reconcile_proposals(
    body: ReconcileProductionProposalsRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return reconcile_production_proposals(session, proposal_ids=body.proposal_ids)


@router.post("/proposals/exported/reconcile", response_model=ProductionProposalReconcileResult)
def post_reconcile_exported_proposals(
    body: ReconcileProductionProposalsRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return reconcile_production_proposals(session, proposal_ids=body.proposal_ids)
