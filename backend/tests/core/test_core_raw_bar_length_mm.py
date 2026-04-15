"""Test mirati per raw_bar_length_mm_enabled (famiglia) e raw_bar_length_mm (articolo) — TASK-V2-118."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import (
    get_articolo_detail,
    list_famiglie_catalog,
    set_articolo_raw_bar_length_mm,
    toggle_famiglia_raw_bar_length_mm_enabled,
)
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401


NOW = datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def _famiglia(code: str, **kwargs) -> ArticoloFamiglia:
    return ArticoloFamiglia(code=code, label=code.capitalize(), is_active=True, **kwargs)


def _articolo(codice: str, **kwargs) -> SyncArticolo:
    return SyncArticolo(codice_articolo=codice, attivo=True, synced_at=NOW, **kwargs)


# ─── famiglia: raw_bar_length_mm_enabled default ──────────────────────────────

def test_famiglia_raw_bar_length_mm_enabled_default_false(session):
    session.add(_famiglia("barre"))
    session.commit()

    rows = list_famiglie_catalog(session)
    assert len(rows) == 1
    assert rows[0].raw_bar_length_mm_enabled is False


def test_toggle_famiglia_raw_bar_length_mm_enabled_true(session):
    session.add(_famiglia("barre"))
    session.commit()

    row = toggle_famiglia_raw_bar_length_mm_enabled(session, "barre")
    session.commit()
    assert row.raw_bar_length_mm_enabled is True


def test_toggle_famiglia_raw_bar_length_mm_enabled_twice(session):
    session.add(_famiglia("barre"))
    session.commit()

    toggle_famiglia_raw_bar_length_mm_enabled(session, "barre")
    session.commit()
    row = toggle_famiglia_raw_bar_length_mm_enabled(session, "barre")
    session.commit()
    assert row.raw_bar_length_mm_enabled is False


def test_toggle_famiglia_raw_bar_length_mm_not_found(session):
    with pytest.raises(ValueError, match="non trovata"):
        toggle_famiglia_raw_bar_length_mm_enabled(session, "inesistente")


# ─── articolo: raw_bar_length_mm ─────────────────────────────────────────────

def test_articolo_raw_bar_length_mm_default_none(session):
    session.add(_articolo("ART001"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.raw_bar_length_mm is None


def test_set_articolo_raw_bar_length_mm(session):
    session.add(_articolo("ART001"))
    session.commit()

    set_articolo_raw_bar_length_mm(session, "ART001", Decimal("3000.0"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.raw_bar_length_mm == Decimal("3000.0")


def test_set_articolo_raw_bar_length_mm_to_none(session):
    session.add(_articolo("ART001"))
    session.commit()

    set_articolo_raw_bar_length_mm(session, "ART001", Decimal("3000.0"))
    session.commit()
    set_articolo_raw_bar_length_mm(session, "ART001", None)
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.raw_bar_length_mm is None


def test_set_articolo_raw_bar_length_mm_creates_config_if_missing(session):
    session.add(_articolo("ART001"))
    session.commit()

    assert session.get(CoreArticoloConfig, "ART001") is None
    set_articolo_raw_bar_length_mm(session, "ART001", Decimal("6000.0"))
    session.commit()
    assert session.get(CoreArticoloConfig, "ART001") is not None


def test_articolo_raw_bar_length_mm_independent_of_famiglia_flag(session):
    """raw_bar_length_mm e esposto anche se la famiglia non ha raw_bar_length_mm_enabled."""
    session.add(_famiglia("barre"))
    config = CoreArticoloConfig(
        codice_articolo="ART001",
        famiglia_code="barre",
        updated_at=NOW,
    )
    session.add(config)
    session.add(_articolo("ART001"))
    session.commit()

    set_articolo_raw_bar_length_mm(session, "ART001", Decimal("2500.0"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.raw_bar_length_mm == Decimal("2500.0")
