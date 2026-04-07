"""
Test di integrazione per il Core slice `articoli` (DL-ARCH-V2-013).

Verificano:
- lista articoli attivi (ordinamento, esclusione inattivi)
- dettaglio articolo esistente e non esistente
- display_label: desc1+desc2, desc1 only, fallback codice
- separazione: il Core legge sync_articoli, non la espone direttamente
- il Core non scrive in sync_articoli
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.articoli.queries import get_articolo_detail, list_articoli


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


NOW = datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc)


def _articolo(
    codice: str,
    desc1: str | None = None,
    desc2: str | None = None,
    um: str | None = None,
    attivo: bool = True,
    **kwargs,
) -> SyncArticolo:
    return SyncArticolo(
        codice_articolo=codice,
        descrizione_1=desc1,
        descrizione_2=desc2,
        unita_misura_codice=um,
        attivo=attivo,
        synced_at=NOW,
        **kwargs,
    )


# ─── Lista articoli ───────────────────────────────────────────────────────────

def test_list_articoli_returns_active_only(session):
    session.add(_articolo("ART001", desc1="Alfa"))
    session.add(_articolo("ART002", desc1="Beta", attivo=False))
    session.commit()

    items = list_articoli(session)
    assert len(items) == 1
    assert items[0].codice_articolo == "ART001"


def test_list_articoli_ordered_by_codice(session):
    session.add(_articolo("ART003", desc1="Gamma"))
    session.add(_articolo("ART001", desc1="Alfa"))
    session.add(_articolo("ART002", desc1="Beta"))
    session.commit()

    items = list_articoli(session)
    codici = [i.codice_articolo for i in items]
    assert codici == ["ART001", "ART002", "ART003"]


def test_list_articoli_empty(session):
    items = list_articoli(session)
    assert items == []


def test_list_articoli_item_fields(session):
    session.add(_articolo("ART001", desc1="Bullone", desc2="M8x20", um="PZ"))
    session.commit()

    items = list_articoli(session)
    item = items[0]
    assert item.descrizione_1 == "Bullone"
    assert item.descrizione_2 == "M8x20"
    assert item.unita_misura_codice == "PZ"
    assert item.display_label == "Bullone M8x20"


# ─── display_label in lista ───────────────────────────────────────────────────

def test_list_display_label_desc1_and_desc2(session):
    session.add(_articolo("ART001", desc1="Bullone", desc2="M8x20"))
    session.commit()
    assert list_articoli(session)[0].display_label == "Bullone M8x20"


def test_list_display_label_desc1_only(session):
    session.add(_articolo("ART001", desc1="Bullone"))
    session.commit()
    assert list_articoli(session)[0].display_label == "Bullone"


def test_list_display_label_fallback_codice(session):
    session.add(_articolo("ART001"))
    session.commit()
    assert list_articoli(session)[0].display_label == "ART001"


# ─── Dettaglio articolo ───────────────────────────────────────────────────────

def test_get_articolo_detail_exists(session):
    session.add(_articolo(
        "ART001",
        desc1="Bullone",
        desc2="M8x20",
        um="PZ",
        categoria_articolo_1="CAT01",
        materiale_grezzo_codice="MAT01",
        quantita_materiale_grezzo_occorrente=Decimal("1.50000"),
        quantita_materiale_grezzo_scarto=Decimal("0.10000"),
        misura_articolo="8x20",
        codice_immagine="IMG",
        contenitori_magazzino="BIN-A1",
        peso_grammi=Decimal("5.00000"),
    ))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.codice_articolo == "ART001"
    assert detail.descrizione_1 == "Bullone"
    assert detail.descrizione_2 == "M8x20"
    assert detail.unita_misura_codice == "PZ"
    assert detail.categoria_articolo_1 == "CAT01"
    assert detail.materiale_grezzo_codice == "MAT01"
    assert detail.quantita_materiale_grezzo_occorrente == Decimal("1.50000")
    assert detail.quantita_materiale_grezzo_scarto == Decimal("0.10000")
    assert detail.misura_articolo == "8x20"
    assert detail.codice_immagine == "IMG"
    assert detail.contenitori_magazzino == "BIN-A1"
    assert detail.peso_grammi == Decimal("5.00000")
    assert detail.display_label == "Bullone M8x20"


def test_get_articolo_detail_not_found(session):
    detail = get_articolo_detail(session, "NONEXISTENT")
    assert detail is None


def test_get_articolo_detail_display_label_desc1_only(session):
    session.add(_articolo("ART001", desc1="Rondella"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.display_label == "Rondella"


def test_get_articolo_detail_display_label_fallback_codice(session):
    session.add(_articolo("ART001"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.display_label == "ART001"


def test_get_articolo_detail_inactive_still_retrievable(session):
    """Il dettaglio e disponibile anche per articoli inattivi (navigazione diretta)."""
    session.add(_articolo("ART001", desc1="Vecchio", attivo=False))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.codice_articolo == "ART001"


# ─── Separazione Core / sync ──────────────────────────────────────────────────

def test_core_does_not_return_sync_model_instances(session):
    """list_articoli e get_articolo_detail restituiscono read model Core, non SyncArticolo."""
    session.add(_articolo("ART001", desc1="Test"))
    session.commit()

    items = list_articoli(session)
    assert not isinstance(items[0], SyncArticolo)

    detail = get_articolo_detail(session, "ART001")
    assert not isinstance(detail, SyncArticolo)


def test_core_queries_do_not_modify_sync_articoli(session):
    """Le query Core non devono modificare sync_articoli."""
    session.add(_articolo("ART001", desc1="Originale"))
    session.commit()

    list_articoli(session)
    get_articolo_detail(session, "ART001")

    row = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert row.descrizione_1 == "Originale"
