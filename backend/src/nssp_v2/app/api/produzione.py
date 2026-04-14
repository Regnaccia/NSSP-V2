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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.core.criticita import CriticitaItem, list_criticita_v1
from nssp_v2.core.planning_candidates import PlanningCandidateItem, list_planning_candidates_v1
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
    set_articolo_stock_policy_override,
    set_famiglia_articolo,
    set_famiglia_stock_policy,
    toggle_famiglia_active,
    toggle_famiglia_aggrega_codice_produzione,
    toggle_famiglia_considera_produzione,
    toggle_famiglia_gestione_scorte,
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
    _: dict = Depends(get_current_user),
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
    return list_planning_candidates_v1(session, customer_horizon_days=horizon_days)


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
