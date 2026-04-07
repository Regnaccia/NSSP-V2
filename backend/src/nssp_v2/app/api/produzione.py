"""
Router surface produzione — Core slice articoli (TASK-V2-020, TASK-V2-022).

Endpoint:
  GET   /api/produzione/articoli                       — lista articoli attivi
  GET   /api/produzione/articoli/{codice}              — dettaglio articolo
  GET   /api/produzione/famiglie                       — catalogo famiglie
  PATCH /api/produzione/articoli/{codice}/famiglia     — imposta famiglia articolo

Tutti gli endpoint richiedono autenticazione Bearer.
Il Core non espone mai i target sync_* grezzi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.core.articoli import (
    ArticoloDetail,
    ArticoloItem,
    FamigliaItem,
    get_articolo_detail,
    list_articoli,
    list_famiglie,
    set_famiglia_articolo,
)
from nssp_v2.shared.db import get_session

router = APIRouter(prefix="/produzione", tags=["produzione"])


class SetFamigliaRequest(BaseModel):
    famiglia_code: str | None = None


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


@router.get("/famiglie", response_model=list[FamigliaItem])
def get_famiglie(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Catalogo famiglie articolo attive, ordinate per sort_order."""
    return list_famiglie(session)


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
    set_famiglia_articolo(session, codice_articolo, body.famiglia_code)
    session.commit()
