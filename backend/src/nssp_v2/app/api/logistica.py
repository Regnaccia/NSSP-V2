"""
Router surface logistica — Core slice clienti + destinazioni (TASK-V2-013).

Endpoint:
  GET   /api/logistica/clienti                                   — lista clienti attivi
  GET   /api/logistica/clienti/{codice_cli}/destinazioni         — destinazioni del cliente
  GET   /api/logistica/destinazioni/{codice_destinazione}        — dettaglio destinazione
  PATCH /api/logistica/destinazioni/{codice_destinazione}/nickname — imposta nickname interno

Tutti gli endpoint richiedono autenticazione Bearer.
Il Core non espone mai i target sync_* grezzi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.core.clienti_destinazioni import (
    ClienteItem,
    DestinazioneDetail,
    DestinazioneItem,
    get_destinazione_detail,
    list_clienti,
    list_destinazioni_per_cliente,
    set_nickname_destinazione,
)
from nssp_v2.shared.db import get_session

router = APIRouter(prefix="/logistica", tags=["logistica"])


class SetNicknameRequest(BaseModel):
    nickname: str | None = None


@router.get("/clienti", response_model=list[ClienteItem])
def get_clienti(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista clienti attivi, ordinata per ragione sociale."""
    return list_clienti(session)


@router.get("/clienti/{codice_cli}/destinazioni", response_model=list[DestinazioneItem])
def get_destinazioni_per_cliente(
    codice_cli: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Destinazioni attive del cliente, con display_label e nickname."""
    return list_destinazioni_per_cliente(session, codice_cli)


@router.get("/destinazioni/{codice_destinazione}", response_model=DestinazioneDetail)
def get_destinazione(
    codice_destinazione: str,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Dettaglio completo della destinazione con ragione_sociale_cliente."""
    detail = get_destinazione_detail(session, codice_destinazione)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destinazione '{codice_destinazione}' non trovata",
        )
    return detail


@router.patch(
    "/destinazioni/{codice_destinazione}/nickname",
    status_code=status.HTTP_204_NO_CONTENT,
)
def patch_nickname(
    codice_destinazione: str,
    body: SetNicknameRequest,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Imposta o rimuove il nickname interno della destinazione.

    Non modifica mai i target sync_*.
    """
    set_nickname_destinazione(session, codice_destinazione, body.nickname)
    session.commit()
