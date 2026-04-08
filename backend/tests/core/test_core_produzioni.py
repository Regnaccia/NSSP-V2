"""
Test di integrazione per il Core slice `produzioni` (TASK-V2-030).

Verificano:
- bucket corretto (active / historical)
- stato_produzione computato dalle quantita
- precedenza di forza_completata sull'override
- aggiornamento del flag forza_completata
- aggregazione da entrambi i mirror
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.produzioni.queries import list_produzioni, set_forza_completata
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica
from nssp_v2.core.produzioni.models import CoreProduzioneOverride

from datetime import datetime, timezone


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 8, 12, 0, 0, tzinfo=timezone.utc)


def _attiva(id_dettaglio: int, qtor=Decimal("100"), qtev=Decimal("0"), **kwargs) -> SyncProduzioneAttiva:
    return SyncProduzioneAttiva(
        id_dettaglio=id_dettaglio,
        cliente_ragione_sociale=kwargs.get("cliente", "ACME SRL"),
        codice_articolo=kwargs.get("codice_articolo", "ART001"),
        descrizione_articolo=kwargs.get("descrizione_articolo", "Bullone"),
        numero_documento=kwargs.get("numero_documento", "DOC01"),
        numero_riga_documento=kwargs.get("numero_riga_documento", 1),
        quantita_ordinata=qtor,
        quantita_prodotta=qtev,
        attivo=True,
        synced_at=_NOW,
    )


def _storica(id_dettaglio: int, qtor=Decimal("100"), qtev=Decimal("100"), **kwargs) -> SyncProduzioneStorica:
    return SyncProduzioneStorica(
        id_dettaglio=id_dettaglio,
        cliente_ragione_sociale=kwargs.get("cliente", "BETA SPA"),
        codice_articolo=kwargs.get("codice_articolo", "ART002"),
        descrizione_articolo=kwargs.get("descrizione_articolo", "Dado"),
        numero_documento=kwargs.get("numero_documento", "DOC02"),
        numero_riga_documento=kwargs.get("numero_riga_documento", 1),
        quantita_ordinata=qtor,
        quantita_prodotta=qtev,
        attivo=True,
        synced_at=_NOW,
    )


# ─── Bucket ───────────────────────────────────────────────────────────────────

def test_bucket_active(session):
    session.add(_attiva(1001))
    session.flush()

    items = list_produzioni(session)
    assert len(items) == 1
    assert items[0].bucket == "active"
    assert items[0].id_dettaglio == 1001


def test_bucket_historical(session):
    session.add(_storica(2001))
    session.flush()

    items = list_produzioni(session)
    assert len(items) == 1
    assert items[0].bucket == "historical"
    assert items[0].id_dettaglio == 2001


def test_bucket_entrambi_presenti(session):
    session.add(_attiva(1001))
    session.add(_storica(2001))
    session.flush()

    items = list_produzioni(session)
    assert len(items) == 2
    buckets = {i.bucket for i in items}
    assert buckets == {"active", "historical"}


def test_ordine_attive_prima_storiche(session):
    session.add(_attiva(1001))
    session.add(_attiva(1002))
    session.add(_storica(2001))
    session.flush()

    items = list_produzioni(session)
    assert items[0].bucket == "active"
    assert items[1].bucket == "active"
    assert items[2].bucket == "historical"


# ─── Stato produzione (regola standard) ───────────────────────────────────────

def test_stato_attiva_quando_qtev_minore(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("50")))
    session.flush()

    item = list_produzioni(session)[0]
    assert item.stato_produzione == "attiva"


def test_stato_completata_quando_qtev_uguale(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("100")))
    session.flush()

    item = list_produzioni(session)[0]
    assert item.stato_produzione == "completata"


def test_stato_completata_quando_qtev_maggiore(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("120")))
    session.flush()

    item = list_produzioni(session)[0]
    assert item.stato_produzione == "completata"


def test_stato_attiva_quando_quantita_none(session):
    obj = _attiva(1001, qtor=None, qtev=None)
    session.add(obj)
    session.flush()

    item = list_produzioni(session)[0]
    assert item.stato_produzione == "attiva"


def test_stato_storica_completata_per_default(session):
    session.add(_storica(2001, qtor=Decimal("100"), qtev=Decimal("100")))
    session.flush()

    item = list_produzioni(session)[0]
    assert item.stato_produzione == "completata"


# ─── Override forza_completata ────────────────────────────────────────────────

def test_forza_completata_default_false(session):
    session.add(_attiva(1001))
    session.flush()

    item = list_produzioni(session)[0]
    assert item.forza_completata is False


def test_forza_completata_override_attiva(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.flush()

    updated = set_forza_completata(session, 1001, "active", True)
    assert updated.forza_completata is True
    assert updated.stato_produzione == "completata"


def test_forza_completata_precedenza_su_quantita(session):
    """Con forza_completata=True, stato=completata anche se qtev < qtor."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    items = list_produzioni(session)
    assert items[0].stato_produzione == "completata"


def test_forza_completata_reset_a_false(session):
    """Reimpostare forza_completata=False ripristina la regola standard."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    set_forza_completata(session, 1001, "active", False)
    items = list_produzioni(session)
    assert items[0].stato_produzione == "attiva"
    assert items[0].forza_completata is False


def test_forza_completata_su_storica(session):
    session.add(_storica(2001, qtor=Decimal("100"), qtev=Decimal("50")))
    session.flush()

    updated = set_forza_completata(session, 2001, "historical", True)
    assert updated.bucket == "historical"
    assert updated.stato_produzione == "completata"


def test_forza_completata_record_inesistente_raises(session):
    with pytest.raises(ValueError, match="non trovata"):
        set_forza_completata(session, 9999, "active", True)


def test_forza_completata_bucket_non_valido_raises(session):
    with pytest.raises(ValueError, match="Bucket non valido"):
        set_forza_completata(session, 1001, "wrong", True)


def test_forza_completata_non_confonde_bucket(session):
    """Override su 'active' non altera la stessa id_dettaglio in 'historical'."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.add(_storica(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    items = list_produzioni(session)

    active_item = next(i for i in items if i.bucket == "active")
    historical_item = next(i for i in items if i.bucket == "historical")

    assert active_item.forza_completata is True
    assert active_item.stato_produzione == "completata"
    assert historical_item.forza_completata is False
    assert historical_item.stato_produzione == "attiva"


# ─── Filtra inattivi ──────────────────────────────────────────────────────────

def test_inattivi_esclusi_dalla_lista(session):
    obj = _attiva(1001)
    obj.attivo = False
    session.add(obj)
    obj2 = _storica(2001)
    obj2.attivo = False
    session.add(obj2)
    session.flush()

    items = list_produzioni(session)
    assert len(items) == 0
