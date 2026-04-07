"""
Test unit per shared/security.py.

Non richiedono DB attivo: testano hash password, verifica e JWT.
"""

from jose import jwt

from nssp_v2.shared.config import settings
from nssp_v2.shared.security import (
    create_access_token,
    decode_access_token,
    get_available_surfaces,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext():
    pw = "mysecretpassword"
    assert hash_password(pw) != pw


def test_verify_password_correct():
    pw = "mysecretpassword"
    assert verify_password(pw, hash_password(pw))


def test_verify_password_wrong():
    assert not verify_password("wrong", hash_password("correct"))


def test_create_and_decode_token():
    data = {
        "sub": "1",
        "username": "admin",
        "roles": ["admin"],
        "access_mode": "browser",
    }
    token = create_access_token(data)
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert payload["roles"] == ["admin"]
    assert payload["access_mode"] == "browser"
    assert "exp" in payload


def test_token_contains_expected_algorithm():
    token = create_access_token({"sub": "1", "roles": []})
    header = jwt.get_unverified_header(token)
    assert header["alg"] == settings.jwt_algorithm


def test_get_available_surfaces_known_roles():
    surfaces = get_available_surfaces(["admin", "produzione"])
    paths = {s["path"] for s in surfaces}
    assert "/admin" in paths
    assert "/produzione" in paths


def test_get_available_surfaces_unknown_role_ignored():
    surfaces = get_available_surfaces(["unknown_role"])
    assert surfaces == []


def test_get_available_surfaces_empty():
    assert get_available_surfaces([]) == []
