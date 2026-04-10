"""
Router surface produzione — Core slice articoli + produzioni (TASK-V2-020, TASK-V2-022, TASK-V2-030).

Endpoint:
  GET   /api/produzione/articoli                                  — lista articoli attivi
  GET   /api/produzione/articoli/{codice}                         — dettaglio articolo
  GET   /api/produzione/famiglie                                  — catalogo famiglie
  PATCH /api/produzione/articoli/{codice}/famiglia                — imposta famiglia articolo
  GET   /api/produzione/produzioni                                — lista produzioni (attive + storiche)
  PATCH /api/produzione/produzioni/{id_dettaglio}/forza-completata — override flag forza_completata

Tutti gli endpoint richiedono autenticazione Bearer.
Il Core non espone mai i target sync_* grezzi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.core.criticita import CriticitaItem, list_criticita_v1
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
    set_famiglia_articolo,
    toggle_famiglia_active,
    toggle_famiglia_considera_produzione,
)
from nssp_v2.shared.db import get_session

router = APIRouter(prefix="/produzione", tags=["produzione"])


class SetForzaCompletataRequest(BaseModel):
    bucket: str
    forza_completata: bool


class SetFamigliaRequest(BaseModel):
    famiglia_code: str | None = None


class CreateFamigliaRequest(BaseModel):
    code: str
    label: str
    sort_order: int | None = None


@router.get("/articoli", response_model=list[ArticoloItem])
def get_articoli(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista articoli attivi con famiglia interna, ordinata per codice_articolo."""
    return list_articoli(session)


@router.get("/articoli/{codice_articolo}", response_model=ArticoloDetail)
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


@router.patch(
    "/articoli/{codice_articolo}/famiglia",
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
