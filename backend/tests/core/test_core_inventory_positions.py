"""
Test di integrazione per il Core slice `inventory_positions` (TASK-V2-037).

Verificano:
- formula di calcolo on_hand_qty = total_load - total_unload
- aggregazione corretta per article_code
- determinismo del rebuild
- comportamento con NULL in quantita
- movement_count e source_last_movement_date corretti
- articoli senza codice_articolo esclusi dall'aggregazione
- get_inventory_position per singolo articolo
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.inventory_positions.queries import (
    rebuild_inventory_positions,
    list_inventory_positions,
    get_inventory_position,
)
from nssp_v2.sync.mag_reale.models import SyncMagReale


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 8, 10, 0, 0, tzinfo=timezone.utc)
_MOV_DATE = datetime(2026, 1, 15, 0, 0, 0)


def _mov(
    id_movimento: int,
    codice_articolo: str | None = "ART001",
    quantita_caricata: str | None = None,
    quantita_scaricata: str | None = None,
    data_movimento: datetime | None = _MOV_DATE,
) -> SyncMagReale:
    return SyncMagReale(
        id_movimento=id_movimento,
        codice_articolo=codice_articolo,
        quantita_caricata=Decimal(quantita_caricata) if quantita_caricata is not None else None,
        quantita_scaricata=Decimal(quantita_scaricata) if quantita_scaricata is not None else None,
        causale_movimento_codice=None,
        data_movimento=data_movimento,
        synced_at=_NOW,
    )


# ─── Formula canonica ─────────────────────────────────────────────────────────

def test_on_hand_qty_carico(session):
    """Solo movimenti di carico: on_hand_qty = total_load."""
    session.add(_mov(1, quantita_caricata="100.000000"))
    session.add(_mov(2, quantita_caricata="50.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")

    assert item is not None
    assert item.total_load_qty == Decimal("150.000000")
    assert item.total_unload_qty == Decimal("0")
    assert item.on_hand_qty == Decimal("150.000000")


def test_on_hand_qty_scarico(session):
    """Solo movimenti di scarico: on_hand_qty negativo."""
    session.add(_mov(1, quantita_scaricata="30.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")

    assert item.total_load_qty == Decimal("0")
    assert item.total_unload_qty == Decimal("30.000000")
    assert item.on_hand_qty == Decimal("-30.000000")


def test_on_hand_qty_carico_e_scarico(session):
    """Formula canonica: load - unload."""
    session.add(_mov(1, quantita_caricata="100.000000"))
    session.add(_mov(2, quantita_scaricata="40.000000"))
    session.add(_mov(3, quantita_caricata="20.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")

    assert item.total_load_qty == Decimal("120.000000")
    assert item.total_unload_qty == Decimal("40.000000")
    assert item.on_hand_qty == Decimal("80.000000")


def test_quantita_none_trattata_come_zero(session):
    """quantita_caricata/scaricata NULL vengono trattate come 0 nella somma."""
    session.add(_mov(1, quantita_caricata="50.000000", quantita_scaricata=None))
    session.add(_mov(2, quantita_caricata=None, quantita_scaricata="10.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")

    assert item.total_load_qty == Decimal("50.000000")
    assert item.total_unload_qty == Decimal("10.000000")
    assert item.on_hand_qty == Decimal("40.000000")


# ─── Aggregazione per articolo ────────────────────────────────────────────────

def test_aggregazione_per_articolo(session):
    """Movimenti di articoli diversi producono righe separate."""
    session.add(_mov(1, codice_articolo="ART001", quantita_caricata="100.000000"))
    session.add(_mov(2, codice_articolo="ART002", quantita_caricata="200.000000"))
    session.add(_mov(3, codice_articolo="ART001", quantita_caricata="50.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 2
    art1 = next(i for i in items if i.article_code == "ART001")
    art2 = next(i for i in items if i.article_code == "ART002")
    assert art1.total_load_qty == Decimal("150.000000")
    assert art2.total_load_qty == Decimal("200.000000")


def test_lista_ordinata_per_article_code(session):
    """list_inventory_positions restituisce i risultati ordinati per article_code."""
    session.add(_mov(1, codice_articolo="ZZZ001", quantita_caricata="10.000000"))
    session.add(_mov(2, codice_articolo="AAA001", quantita_caricata="20.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 2
    assert items[0].article_code == "AAA001"
    assert items[1].article_code == "ZZZ001"


def test_articoli_senza_codice_esclusi(session):
    """I movimenti con codice_articolo = NULL non contribuiscono a nessuna posizione."""
    session.add(_mov(1, codice_articolo=None, quantita_caricata="999.000000"))
    session.add(_mov(2, codice_articolo="ART001", quantita_caricata="50.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 1
    assert items[0].article_code == "ART001"


# ─── movement_count e source_last_movement_date ───────────────────────────────

def test_movement_count(session):
    """movement_count conta i movimenti aggregati per articolo."""
    for i in range(1, 6):
        session.add(_mov(i, quantita_caricata="10.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")
    assert item.movement_count == 5


def test_source_last_movement_date(session):
    """source_last_movement_date e la data del movimento piu recente."""
    d1 = datetime(2026, 1, 10)
    d2 = datetime(2026, 3, 15)
    d3 = datetime(2026, 2, 20)
    session.add(_mov(1, quantita_caricata="10.000000", data_movimento=d1))
    session.add(_mov(2, quantita_scaricata="5.000000", data_movimento=d2))
    session.add(_mov(3, quantita_caricata="20.000000", data_movimento=d3))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")
    assert item.source_last_movement_date == d2


def test_source_last_movement_date_none_se_tutte_none(session):
    """Se tutti i movimenti hanno data NULL, source_last_movement_date e None."""
    session.add(_mov(1, quantita_caricata="10.000000", data_movimento=None))
    session.flush()

    rebuild_inventory_positions(session)
    item = get_inventory_position(session, "ART001")
    assert item.source_last_movement_date is None


# ─── Determinismo del rebuild ─────────────────────────────────────────────────

def test_rebuild_deterministico(session):
    """Due rebuild consecutivi con stesso input producono lo stesso output."""
    session.add(_mov(1, quantita_caricata="100.000000"))
    session.add(_mov(2, quantita_scaricata="30.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    first = get_inventory_position(session, "ART001")

    rebuild_inventory_positions(session)
    second = get_inventory_position(session, "ART001")

    assert first.on_hand_qty == second.on_hand_qty
    assert first.total_load_qty == second.total_load_qty
    assert first.total_unload_qty == second.total_unload_qty
    assert first.movement_count == second.movement_count


def test_rebuild_ricalcola_dopo_nuovi_movimenti(session):
    """Dopo l'aggiunta di nuovi movimenti, un nuovo rebuild aggiorna la giacenza."""
    session.add(_mov(1, quantita_caricata="100.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    first = get_inventory_position(session, "ART001")
    assert first.on_hand_qty == Decimal("100.000000")

    # Aggiunge un nuovo movimento e ricostruisce
    session.add(_mov(2, quantita_scaricata="40.000000"))
    session.flush()
    rebuild_inventory_positions(session)

    second = get_inventory_position(session, "ART001")
    assert second.on_hand_qty == Decimal("60.000000")
    assert second.movement_count == 2


def test_rebuild_rimuove_articoli_spariti(session):
    """Un rebuild dopo la rimozione di movimenti elimina le posizioni obsolete."""
    session.add(_mov(1, codice_articolo="ART001", quantita_caricata="10.000000"))
    session.add(_mov(2, codice_articolo="ART002", quantita_caricata="20.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    assert len(list_inventory_positions(session)) == 2

    # Rimuoviamo i movimenti di ART002 dal mirror (scenario teorico rebuild)
    session.query(SyncMagReale).filter(SyncMagReale.codice_articolo == "ART002").delete(
        synchronize_session=False
    )
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)
    assert len(items) == 1
    assert items[0].article_code == "ART001"


# ─── Mirror vuoto ─────────────────────────────────────────────────────────────

def test_mirror_vuoto_nessuna_posizione(session):
    """Con mirror vuoto, il rebuild produce 0 posizioni inventariali."""
    count = rebuild_inventory_positions(session)
    assert count == 0
    assert list_inventory_positions(session) == []


def test_get_articolo_inesistente_none(session):
    """get_inventory_position restituisce None se l'articolo non ha posizione."""
    rebuild_inventory_positions(session)
    assert get_inventory_position(session, "INESISTENTE") is None


# ─── Normalizzazione article_code cross-source (TASK-V2-052) ─────────────────

def test_rebuild_normalizza_lowercase(session):
    """rebuild_inventory_positions normalizza codice_articolo lowercase -> uppercase."""
    session.add(_mov(1, codice_articolo="art001", quantita_caricata="100.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 1
    assert items[0].article_code == "ART001"


def test_rebuild_normalizza_spazi_esterni(session):
    """rebuild_inventory_positions rimuove gli spazi esterni dal codice_articolo."""
    session.add(_mov(1, codice_articolo="  ART001  ", quantita_caricata="100.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 1
    assert items[0].article_code == "ART001"


def test_rebuild_chiave_canonica_con_codice_misto(session):
    """rebuild_inventory_positions scrive la chiave canonica (uppercase, trimmed) nel Core.

    Il sync_mag_reale normalizza già al momento della sync, ma il Core applica
    normalize_article_code in modo difensivo per garantire la chiave canonica
    indipendentemente da come il mirror è stato popolato (es. test, migrazione).
    """
    session.add(_mov(1, codice_articolo="art001", quantita_caricata="100.000000"))
    session.add(_mov(2, codice_articolo="art001", quantita_caricata="50.000000"))
    session.flush()

    rebuild_inventory_positions(session)
    items = list_inventory_positions(session)

    assert len(items) == 1
    assert items[0].article_code == "ART001"
    assert items[0].total_load_qty == Decimal("150.000000")


def test_get_inventory_position_normalizza_input_lowercase(session):
    """get_inventory_position trova la posizione anche con input lowercase."""
    session.add(_mov(1, codice_articolo="ART001", quantita_caricata="100.000000"))
    session.flush()
    rebuild_inventory_positions(session)

    item = get_inventory_position(session, "art001")
    assert item is not None
    assert item.on_hand_qty == Decimal("100.000000")


def test_get_inventory_position_normalizza_input_con_spazi(session):
    """get_inventory_position trova la posizione anche con input con spazi."""
    session.add(_mov(1, codice_articolo="ART001", quantita_caricata="100.000000"))
    session.flush()
    rebuild_inventory_positions(session)

    item = get_inventory_position(session, "  ART001  ")
    assert item is not None
    assert item.on_hand_qty == Decimal("100.000000")
