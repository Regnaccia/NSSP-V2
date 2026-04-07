"""
Test di integrazione del Core slice `clienti + destinazioni` con SQLite in-memory.

Non richiedono PostgreSQL attivo.
Verificano:
- join clienti/destinazioni
- display_label e fallback
- separazione dati Easy / dati interni (nickname)
- set_nickname_destinazione
- dettaglio destinazione con ragione_sociale_cliente
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.clienti.models import SyncCliente
from nssp_v2.sync.destinazioni.models import SyncDestinazione
from nssp_v2.core.clienti_destinazioni.models import CoreDestinazioneConfig
from nssp_v2.core.clienti_destinazioni.queries import (
    get_destinazione_detail,
    list_clienti,
    list_destinazioni_per_cliente,
    set_nickname_destinazione,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


NOW = datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc)


def _cliente(codice_cli: str, ragione_sociale: str, attivo: bool = True) -> SyncCliente:
    return SyncCliente(
        codice_cli=codice_cli,
        ragione_sociale=ragione_sociale,
        attivo=attivo,
        synced_at=NOW,
    )


def _destinazione(
    codice_destinazione: str,
    codice_cli: str | None = None,
    indirizzo: str | None = None,
    citta: str | None = None,
    provincia: str | None = None,
    attivo: bool = True,
) -> SyncDestinazione:
    return SyncDestinazione(
        codice_destinazione=codice_destinazione,
        codice_cli=codice_cli,
        indirizzo=indirizzo,
        citta=citta,
        provincia=provincia,
        attivo=attivo,
        synced_at=NOW,
    )


# ─── list_clienti ─────────────────────────────────────────────────────────────

def test_list_clienti_returns_active_only(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_cliente("C002", "Beta Spa", attivo=False))
    session.commit()

    items = list_clienti(session)
    assert len(items) == 1
    assert items[0].codice_cli == "C001"


def test_list_clienti_empty(session):
    assert list_clienti(session) == []


def test_list_clienti_sorted_by_ragione_sociale(session):
    session.add(_cliente("C002", "Zeta Srl"))
    session.add(_cliente("C001", "Alfa Spa"))
    session.commit()

    items = list_clienti(session)
    assert items[0].ragione_sociale == "Alfa Spa"
    assert items[1].ragione_sociale == "Zeta Srl"


# ─── list_destinazioni_per_cliente ───────────────────────────────────────────

def test_list_destinazioni_per_cliente_returns_correct_client(session):
    session.add(_destinazione("D001", codice_cli="C001"))
    session.add(_destinazione("D002", codice_cli="C002"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert len(items) == 1
    assert items[0].codice_destinazione == "D001"


def test_list_destinazioni_excludes_inactive(session):
    session.add(_destinazione("D001", codice_cli="C001"))
    session.add(_destinazione("D002", codice_cli="C001", attivo=False))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert len(items) == 1
    assert items[0].codice_destinazione == "D001"


def test_list_destinazioni_empty_when_no_match(session):
    session.add(_destinazione("D001", codice_cli="C002"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items == []


def test_list_destinazioni_display_label_uses_nickname(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1"))
    config = CoreDestinazioneConfig(
        codice_destinazione="D001",
        nickname_destinazione="Sede Nord",
        updated_at=NOW,
    )
    session.add(config)
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items[0].nickname_destinazione == "Sede Nord"
    assert items[0].display_label == "Sede Nord"


def test_list_destinazioni_display_label_fallback_indirizzo(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items[0].nickname_destinazione is None
    assert items[0].display_label == "Via Roma 1"


def test_list_destinazioni_display_label_fallback_codice(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo=None))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items[0].display_label == "D001"


# ─── get_destinazione_detail ─────────────────────────────────────────────────

def test_get_destinazione_detail_returns_none_for_unknown(session):
    assert get_destinazione_detail(session, "DOESNOTEXIST") is None


def test_get_destinazione_detail_basic(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1", citta="Milano", provincia="MI"))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail is not None
    assert detail.codice_destinazione == "D001"
    assert detail.citta == "Milano"
    assert detail.provincia == "MI"


def test_get_destinazione_detail_joins_ragione_sociale(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail.ragione_sociale_cliente == "Acme Srl"


def test_get_destinazione_detail_ragione_sociale_none_when_no_cliente(session):
    session.add(_destinazione("D001", codice_cli=None))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail.ragione_sociale_cliente is None


def test_get_destinazione_detail_nickname_from_core(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1"))
    session.add(CoreDestinazioneConfig(
        codice_destinazione="D001",
        nickname_destinazione="HUB Ovest",
        updated_at=NOW,
    ))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail.nickname_destinazione == "HUB Ovest"
    assert detail.display_label == "HUB Ovest"


def test_get_destinazione_detail_display_label_fallback(session):
    session.add(_destinazione("D001", codice_cli=None, indirizzo=None))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail.display_label == "D001"


# ─── set_nickname_destinazione ───────────────────────────────────────────────

def test_set_nickname_creates_config(session):
    set_nickname_destinazione(session, "D001", "Sede Principale")
    session.commit()

    config = session.get(CoreDestinazioneConfig, "D001")
    assert config is not None
    assert config.nickname_destinazione == "Sede Principale"


def test_set_nickname_updates_existing(session):
    session.add(CoreDestinazioneConfig(
        codice_destinazione="D001",
        nickname_destinazione="Vecchio",
        updated_at=NOW,
    ))
    session.commit()

    set_nickname_destinazione(session, "D001", "Nuovo")
    session.commit()

    config = session.get(CoreDestinazioneConfig, "D001")
    assert config.nickname_destinazione == "Nuovo"


def test_set_nickname_to_none_clears_value(session):
    session.add(CoreDestinazioneConfig(
        codice_destinazione="D001",
        nickname_destinazione="Sede",
        updated_at=NOW,
    ))
    session.commit()

    set_nickname_destinazione(session, "D001", None)
    session.commit()

    config = session.get(CoreDestinazioneConfig, "D001")
    assert config.nickname_destinazione is None


def test_set_nickname_does_not_modify_sync_tables(session):
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1"))
    session.commit()

    set_nickname_destinazione(session, "D001", "Sede")
    session.commit()

    dest = session.query(SyncDestinazione).filter_by(codice_destinazione="D001").one()
    assert dest.indirizzo == "Via Roma 1"  # sync non modificato


# ─── Separazione Easy / interno nel dettaglio ────────────────────────────────

def test_detail_easy_fields_unchanged_after_set_nickname(session):
    """Impostare nickname non altera i campi Easy nel detail."""
    session.add(_destinazione("D001", codice_cli="C001", indirizzo="Via Roma 1", citta="Milano"))
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()

    set_nickname_destinazione(session, "D001", "Sede Milano")
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail.indirizzo == "Via Roma 1"
    assert detail.citta == "Milano"
    assert detail.ragione_sociale_cliente == "Acme Srl"
    assert detail.nickname_destinazione == "Sede Milano"
    assert detail.display_label == "Sede Milano"
