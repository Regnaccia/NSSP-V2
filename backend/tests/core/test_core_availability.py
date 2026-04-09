"""
Test di integrazione per il Core slice `availability` (TASK-V2-049, DL-ARCH-V2-021).

Verificano:
- formula canonica: availability_qty = inventory_qty - customer_set_aside_qty - committed_qty
- fact mancanti per articolo valgono 0
- availability_qty puo essere negativa (nessun clamp)
- un articolo per riga (UniqueConstraint)
- aggregazione per articolo (piu righe commitment/set_aside sullo stesso articolo)
- articoli distinti trattati separatamente
- rebuild deterministico: stesso input, stesso output
- rebuild ricalcola dopo aggiornamento dei fact sorgente
- mirror vuoti -> 0 righe
- get_availability per singolo articolo
- list_availability ordine per article_code
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.availability.queries import (
    rebuild_availability,
    list_availability,
    get_availability,
)
# Importati per registrare tutti i modelli in Base.metadata prima di create_all
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


# ─── Helper di inserimento diretto nei fact sorgente ──────────────────────────

def _insert_inventory(session, article_code: str, on_hand_qty: str) -> None:
    """Inserisce direttamente in core_inventory_positions."""
    qty = Decimal(on_hand_qty)
    session.add(CoreInventoryPosition(
        article_code=article_code,
        total_load_qty=qty,
        total_unload_qty=Decimal("0"),
        on_hand_qty=qty,
        movement_count=1,
        computed_at=_NOW,
        source_last_movement_date=None,
    ))
    session.flush()


def _insert_set_aside(session, article_code: str, set_aside_qty: str) -> None:
    """Inserisce direttamente in core_customer_set_aside."""
    session.add(CoreCustomerSetAside(
        article_code=article_code,
        source_type="customer_order",
        source_reference=f"{article_code}/1",
        set_aside_qty=Decimal(set_aside_qty),
        computed_at=_NOW,
    ))
    session.flush()


def _insert_commitment(session, article_code: str, committed_qty: str, ref: str = "REF/1") -> None:
    """Inserisce direttamente in core_commitments."""
    session.add(CoreCommitment(
        article_code=article_code,
        source_type="customer_order",
        source_reference=ref,
        committed_qty=Decimal(committed_qty),
        computed_at=_NOW,
    ))
    session.flush()


# ─── Test formula base ────────────────────────────────────────────────────────

def test_formula_canonica(session):
    """availability_qty = inventory_qty - customer_set_aside_qty - committed_qty."""
    _insert_inventory(session, "ART001", "100")
    _insert_set_aside(session, "ART001", "15")
    _insert_commitment(session, "ART001", "30")

    count = rebuild_availability(session)
    assert count == 1

    item = get_availability(session, "ART001")
    assert item is not None
    assert item.inventory_qty == Decimal("100")
    assert item.customer_set_aside_qty == Decimal("15")
    assert item.committed_qty == Decimal("30")
    assert item.availability_qty == Decimal("55")


def test_availability_negativa_ammessa(session):
    """availability_qty puo risultare negativa (nessun clamp a zero)."""
    _insert_inventory(session, "ART001", "10")
    _insert_set_aside(session, "ART001", "20")
    _insert_commitment(session, "ART001", "50")

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.availability_qty == Decimal("-60")


# ─── Test fact mancanti = 0 ───────────────────────────────────────────────────

def test_solo_inventory_set_aside_e_committed_zero(session):
    """Articolo con solo inventory: set_aside=0, committed=0."""
    _insert_inventory(session, "ART001", "80")

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.customer_set_aside_qty == Decimal("0")
    assert item.committed_qty == Decimal("0")
    assert item.availability_qty == Decimal("80")


def test_solo_set_aside_inventory_e_committed_zero(session):
    """Articolo con solo set_aside: inventory=0, committed=0."""
    _insert_set_aside(session, "ART001", "30")

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.inventory_qty == Decimal("0")
    assert item.committed_qty == Decimal("0")
    assert item.availability_qty == Decimal("-30")


def test_solo_committed_inventory_e_set_aside_zero(session):
    """Articolo con solo committed: inventory=0, set_aside=0."""
    _insert_commitment(session, "ART001", "25")

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.inventory_qty == Decimal("0")
    assert item.customer_set_aside_qty == Decimal("0")
    assert item.availability_qty == Decimal("-25")


def test_tutti_zero_nessun_articolo(session):
    """Mirror tutti vuoti -> rebuild ritorna 0 righe."""
    count = rebuild_availability(session)
    assert count == 0
    assert list_availability(session) == []


# ─── Test aggregazione multi-riga ─────────────────────────────────────────────

def test_piu_commitment_stesso_articolo_aggregati(session):
    """Piu righe commitment per lo stesso articolo vengono sommate."""
    _insert_inventory(session, "ART001", "100")
    _insert_commitment(session, "ART001", "20", ref="ORD/1")
    _insert_commitment(session, "ART001", "30", ref="ORD/2")

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.committed_qty == Decimal("50")
    assert item.availability_qty == Decimal("50")


def test_piu_set_aside_stesso_articolo_aggregati(session):
    """Piu righe set_aside per lo stesso articolo vengono sommate."""
    _insert_inventory(session, "ART001", "100")
    _insert_set_aside(session, "ART001", "10")

    # Seconda riga set_aside con reference diversa
    session.add(CoreCustomerSetAside(
        article_code="ART001",
        source_type="customer_order",
        source_reference="ART001/2",
        set_aside_qty=Decimal("5"),
        computed_at=_NOW,
    ))
    session.flush()

    rebuild_availability(session)

    item = get_availability(session, "ART001")
    assert item.customer_set_aside_qty == Decimal("15")
    assert item.availability_qty == Decimal("85")


# ─── Test articoli distinti ───────────────────────────────────────────────────

def test_articoli_distinti_trattati_separatamente(session):
    """Articoli diversi producono righe availability separate."""
    _insert_inventory(session, "ART001", "100")
    _insert_inventory(session, "ART002", "50")
    _insert_commitment(session, "ART001", "30")
    _insert_set_aside(session, "ART002", "10")

    count = rebuild_availability(session)
    assert count == 2

    a1 = get_availability(session, "ART001")
    assert a1.availability_qty == Decimal("70")

    a2 = get_availability(session, "ART002")
    assert a2.availability_qty == Decimal("40")


def test_rebuild_unifica_article_code_mixed_case(session):
    """Fact con article_code misti convergono in una sola availability canonica."""
    _insert_inventory(session, "ART001", "100")
    _insert_set_aside(session, " art001 ", "15")
    _insert_commitment(session, "art001", "30")

    count = rebuild_availability(session)
    assert count == 1

    item = get_availability(session, " art001 ")
    assert item is not None
    assert item.article_code == "ART001"
    assert item.inventory_qty == Decimal("100")
    assert item.customer_set_aside_qty == Decimal("15")
    assert item.committed_qty == Decimal("30")
    assert item.availability_qty == Decimal("55")


# ─── Test determinismo ────────────────────────────────────────────────────────

def test_rebuild_deterministico(session):
    """Stessa sorgente -> stesso risultato a ogni rebuild."""
    _insert_inventory(session, "ART001", "100")
    _insert_set_aside(session, "ART001", "15")
    _insert_commitment(session, "ART001", "30")

    rebuild_availability(session)
    first = get_availability(session, "ART001")

    rebuild_availability(session)
    second = get_availability(session, "ART001")

    assert first.availability_qty == second.availability_qty
    assert second.inventory_qty == Decimal("100")
    assert second.customer_set_aside_qty == Decimal("15")
    assert second.committed_qty == Decimal("30")


def test_rebuild_aggiorna_dopo_modifica_sorgente(session):
    """Rebuild ricalcola quando i fact sorgente cambiano."""
    _insert_inventory(session, "ART001", "100")
    _insert_commitment(session, "ART001", "20")

    rebuild_availability(session)
    assert get_availability(session, "ART001").availability_qty == Decimal("80")

    # Aggiunge set_aside
    _insert_set_aside(session, "ART001", "15")
    rebuild_availability(session)
    assert get_availability(session, "ART001").availability_qty == Decimal("65")


def test_rebuild_rimuove_articolo_non_piu_presente(session):
    """Rebuild elimina articoli non piu presenti in nessun fact sorgente."""
    _insert_inventory(session, "ART001", "100")
    _insert_commitment(session, "ART002", "10")

    rebuild_availability(session)
    assert len(list_availability(session)) == 2

    # Svuota completamente i fact sorgente e rebuilda
    session.query(CoreInventoryPosition).delete(synchronize_session=False)
    session.query(CoreCommitment).delete(synchronize_session=False)
    session.flush()

    count = rebuild_availability(session)
    assert count == 0
    assert list_availability(session) == []


# ─── Test read model ──────────────────────────────────────────────────────────

def test_get_availability_articolo_assente(session):
    """get_availability ritorna None per articolo non presente."""
    assert get_availability(session, "NONEXISTENT") is None


def test_list_availability_ordinata_per_article_code(session):
    """list_availability ritorna le righe ordinate per article_code."""
    _insert_inventory(session, "ZZZ", "10")
    _insert_inventory(session, "AAA", "20")
    _insert_inventory(session, "MMM", "15")

    rebuild_availability(session)

    items = list_availability(session)
    assert [i.article_code for i in items] == ["AAA", "MMM", "ZZZ"]
