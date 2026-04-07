"""
Test di integrazione per la famiglia articolo (DL-ARCH-V2-014).

Verificano:
- seed iniziale del catalogo famiglie
- associazione articolo -> famiglia
- esposizione famiglia nel contratto Core/API
- nessuna write nel layer sync_articoli
- rimozione associazione (famiglia_code=None)
- articoli senza famiglia restano funzionanti
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import (
    get_articolo_detail,
    list_articoli,
    list_famiglie,
    set_famiglia_articolo,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


NOW = datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc)

FAMIGLIE_SEED = [
    ("materia_prima",     "Materia prima",     1),
    ("articolo_standard", "Articolo standard", 2),
    ("speciale",          "Speciale",          3),
    ("barre",             "Barre",             4),
    ("conto_lavorazione", "Conto lavorazione", 5),
]


def _seed_famiglie(session: Session) -> None:
    for code, label, order in FAMIGLIE_SEED:
        session.add(ArticoloFamiglia(code=code, label=label, sort_order=order, is_active=True))
    session.commit()


def _articolo(codice: str, desc1: str | None = None) -> SyncArticolo:
    return SyncArticolo(
        codice_articolo=codice,
        descrizione_1=desc1,
        attivo=True,
        synced_at=NOW,
    )


# ─── Catalogo famiglie ────────────────────────────────────────────────────────

def test_list_famiglie_returns_all_active(session):
    _seed_famiglie(session)
    items = list_famiglie(session)
    assert len(items) == 5


def test_list_famiglie_contains_seed_values(session):
    _seed_famiglie(session)
    codes = {f.code for f in list_famiglie(session)}
    assert codes == {"materia_prima", "articolo_standard", "speciale", "barre", "conto_lavorazione"}


def test_list_famiglie_ordered_by_sort_order(session):
    _seed_famiglie(session)
    items = list_famiglie(session)
    orders = [f.sort_order for f in items]
    assert orders == sorted(orders)


def test_list_famiglie_excludes_inactive(session):
    _seed_famiglie(session)
    # Disattiva una famiglia
    fam = session.query(ArticoloFamiglia).filter_by(code="speciale").one()
    fam.is_active = False
    session.commit()

    items = list_famiglie(session)
    codes = {f.code for f in items}
    assert "speciale" not in codes
    assert len(items) == 4


# ─── Associazione articolo -> famiglia ───────────────────────────────────────

def test_set_famiglia_articolo_crea_config(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    set_famiglia_articolo(session, "ART001", "materia_prima")
    session.commit()

    config = session.get(CoreArticoloConfig, "ART001")
    assert config is not None
    assert config.famiglia_code == "materia_prima"


def test_set_famiglia_articolo_aggiorna_config(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    set_famiglia_articolo(session, "ART001", "materia_prima")
    session.commit()
    set_famiglia_articolo(session, "ART001", "barre")
    session.commit()

    config = session.get(CoreArticoloConfig, "ART001")
    assert config.famiglia_code == "barre"


def test_set_famiglia_articolo_rimuove_associazione(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    set_famiglia_articolo(session, "ART001", "barre")
    session.commit()
    set_famiglia_articolo(session, "ART001", None)
    session.commit()

    config = session.get(CoreArticoloConfig, "ART001")
    assert config.famiglia_code is None


def test_set_famiglia_non_modifica_sync_articoli(session):
    """set_famiglia_articolo non deve mai scrivere in sync_articoli."""
    _seed_famiglie(session)
    session.add(_articolo("ART001", desc1="Originale"))
    session.commit()

    set_famiglia_articolo(session, "ART001", "materia_prima")
    session.commit()

    art = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert art.descrizione_1 == "Originale"


# ─── Esposizione famiglia nel contratto Core/API ──────────────────────────────

def test_list_articoli_espone_famiglia(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()
    set_famiglia_articolo(session, "ART001", "articolo_standard")
    session.commit()

    items = list_articoli(session)
    item = items[0]
    assert item.famiglia_code == "articolo_standard"
    assert item.famiglia_label == "Articolo standard"


def test_list_articoli_famiglia_none_se_non_assegnata(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    items = list_articoli(session)
    assert items[0].famiglia_code is None
    assert items[0].famiglia_label is None


def test_get_articolo_detail_espone_famiglia(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001", desc1="Bullone"))
    session.commit()
    set_famiglia_articolo(session, "ART001", "speciale")
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.famiglia_code == "speciale"
    assert detail.famiglia_label == "Speciale"


def test_get_articolo_detail_famiglia_none_se_non_assegnata(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.famiglia_code is None
    assert detail.famiglia_label is None


# ─── Articoli senza famiglia restano funzionanti ──────────────────────────────

def test_list_articoli_funziona_senza_famiglie_seeded(session):
    """La lista articoli funziona anche se il catalogo famiglie e vuoto."""
    session.add(_articolo("ART001", desc1="Test"))
    session.commit()

    items = list_articoli(session)
    assert len(items) == 1
    assert items[0].famiglia_code is None


def test_get_articolo_detail_funziona_senza_famiglia(session):
    session.add(_articolo("ART001"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.famiglia_code is None


# ─── Idempotenza ──────────────────────────────────────────────────────────────

def test_set_famiglia_idempotente(session):
    _seed_famiglie(session)
    session.add(_articolo("ART001"))
    session.commit()

    set_famiglia_articolo(session, "ART001", "barre")
    session.commit()
    set_famiglia_articolo(session, "ART001", "barre")
    session.commit()

    assert session.query(CoreArticoloConfig).count() == 1
    assert session.get(CoreArticoloConfig, "ART001").famiglia_code == "barre"
