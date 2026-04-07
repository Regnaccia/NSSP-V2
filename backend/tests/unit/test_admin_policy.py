"""
Test unit per app/services/admin_policy.py.

Funzioni pure: non richiedono DB attivo.
"""

import pytest
from fastapi import HTTPException

from nssp_v2.app.services.admin_policy import assert_not_last_active_admin


def test_allows_deactivation_when_other_admins_exist():
    """Se ci sono altri admin attivi, la disattivazione è permessa."""
    assert_not_last_active_admin(
        target_user_id=1,
        active_admin_user_ids=[1, 2, 3],
    )


def test_blocks_deactivation_when_only_admin():
    """Se l'utente è l'unico admin attivo, la disattivazione viene bloccata."""
    with pytest.raises(HTTPException) as exc_info:
        assert_not_last_active_admin(
            target_user_id=1,
            active_admin_user_ids=[1],
        )
    assert exc_info.value.status_code == 422


def test_blocks_deactivation_when_no_other_active_admins():
    """Lista con solo il target: nessun altro admin rimane."""
    with pytest.raises(HTTPException) as exc_info:
        assert_not_last_active_admin(
            target_user_id=5,
            active_admin_user_ids=[5],
        )
    assert exc_info.value.status_code == 422


def test_blocks_when_active_admin_list_is_empty_except_target():
    """Anche con lista più ampia, se solo il target è admin attivo viene bloccato."""
    with pytest.raises(HTTPException):
        assert_not_last_active_admin(
            target_user_id=42,
            active_admin_user_ids=[42],
        )


def test_allows_operation_when_two_admins_and_target_is_one():
    """Con due admin, rimuovere uno è ammesso."""
    assert_not_last_active_admin(
        target_user_id=10,
        active_admin_user_ids=[10, 20],
    )


def test_error_message_is_descriptive():
    """Il messaggio di errore è leggibile."""
    with pytest.raises(HTTPException) as exc_info:
        assert_not_last_active_admin(1, [1])
    assert "ultimo admin" in exc_info.value.detail.lower()
