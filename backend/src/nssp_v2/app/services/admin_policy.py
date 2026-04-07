"""
Policy funzioni pure per la surface admin.

Funzioni pure: non dipendono dalla sessione DB, ricevono dati già estratti.
Questo le rende testabili in isolamento senza DB attivo.

Policy implementate (DL-ARCH-V2-006 §6):
- impossibile rimuovere l'ultimo admin attivo
"""

from fastapi import HTTPException, status


def assert_not_last_active_admin(
    target_user_id: int,
    active_admin_user_ids: list[int],
) -> None:
    """Lancia 422 se l'operazione rimuoverebbe l'ultimo admin attivo.

    Da chiamare prima di:
    - disattivare un utente che ha ruolo admin
    - rimuovere il ruolo admin da un utente

    Args:
        target_user_id: ID dell'utente su cui si sta operando.
        active_admin_user_ids: lista degli ID utente attivi con ruolo admin,
                               incluso il target (viene escluso internamente).
    """
    remaining = [uid for uid in active_admin_user_ids if uid != target_user_id]
    if not remaining:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Impossibile: sarebbe rimosso l'ultimo admin attivo",
        )
