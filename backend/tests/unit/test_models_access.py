"""
Test unit sui modelli access control.

Non richiedono DB attivo: verificano solo struttura e metadati SQLAlchemy.
"""

from nssp_v2.app.models.access import Role, User, UserRole


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_role_table_name():
    assert Role.__tablename__ == "roles"


def test_user_role_table_name():
    assert UserRole.__tablename__ == "user_roles"


def test_user_has_required_columns():
    cols = {c.name for c in User.__table__.columns}
    assert {"id", "username", "password_hash", "attivo", "created_at"} <= cols


def test_role_has_required_columns():
    cols = {c.name for c in Role.__table__.columns}
    assert {"id", "name"} <= cols


def test_user_role_has_required_columns():
    cols = {c.name for c in UserRole.__table__.columns}
    assert {"user_id", "role_id"} <= cols


def test_user_username_is_unique():
    unique_constraints = {
        c.columns.keys()[0]
        for c in User.__table__.constraints
        if hasattr(c, "columns") and len(list(c.columns)) == 1
    }
    assert "username" in unique_constraints


def test_role_name_is_unique():
    unique_constraints = {
        c.columns.keys()[0]
        for c in Role.__table__.constraints
        if hasattr(c, "columns") and len(list(c.columns)) == 1
    }
    assert "name" in unique_constraints


def test_user_role_primary_key_is_composite():
    pk_cols = {c.name for c in UserRole.__table__.primary_key.columns}
    assert pk_cols == {"user_id", "role_id"}
