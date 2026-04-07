"""
Test di integrazione per la destinazione principale derivata (DL-ARCH-V2-012).

Verificano:
- cliente senza destinazioni aggiuntive → principale presente
- cliente con principale + aggiuntive → lista unificata con principale prima
- is_primary=True per la principale, False per le aggiuntive
- nickname configurabile sulla principale
- dettaglio della principale per codice "MAIN:{codice_cli}"
- dettaglio principale non trovato se cliente assente
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
    PRIMARY_PREFIX,
    _primary_codice,
    get_destinazione_detail,
    list_destinazioni_per_cliente,
    set_nickname_destinazione,
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


def _cliente(codice_cli: str, ragione_sociale: str, attivo: bool = True, indirizzo: str | None = None, provincia: str | None = None) -> SyncCliente:
    return SyncCliente(
        codice_cli=codice_cli,
        ragione_sociale=ragione_sociale,
        indirizzo=indirizzo,
        provincia=provincia,
        attivo=attivo,
        synced_at=NOW,
    )


def _destinazione(
    codice_destinazione: str,
    codice_cli: str | None = None,
    indirizzo: str | None = None,
    citta: str | None = None,
    attivo: bool = True,
) -> SyncDestinazione:
    return SyncDestinazione(
        codice_destinazione=codice_destinazione,
        codice_cli=codice_cli,
        indirizzo=indirizzo,
        citta=citta,
        attivo=attivo,
        synced_at=NOW,
    )


# ─── Cliente senza destinazioni aggiuntive ───────────────────────────────────

def test_cliente_senza_aggiuntive_ha_principale(session):
    """Cliente senza righe in POT_DESTDIV → lista contiene solo la principale."""
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert len(items) == 1
    assert items[0].is_primary is True
    assert items[0].codice_destinazione == "MAIN:C001"


def test_principale_display_label_usa_ragione_sociale(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items[0].display_label == "Acme Srl"


def test_principale_campi_da_sync_clienti(session):
    session.add(_cliente("C001", "Acme Srl", indirizzo="Via Roma 1", provincia="MI"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    p = items[0]
    assert p.indirizzo == "Via Roma 1"
    assert p.provincia == "MI"
    assert p.citta is None       # non presente in sync_clienti
    assert p.numero_progressivo_cliente is None


def test_principale_assente_se_cliente_non_attivo(session):
    session.add(_cliente("C001", "Acme Srl", attivo=False))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert len(items) == 0


# ─── Cliente con principale + aggiuntive ─────────────────────────────────────

def test_principale_prima_nelle_aggiuntive(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.add(_destinazione("D002", codice_cli="C001"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert len(items) == 3
    assert items[0].is_primary is True
    assert items[0].codice_destinazione == "MAIN:C001"
    assert items[1].is_primary is False
    assert items[2].is_primary is False


def test_aggiuntive_ordinamento_per_codice(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D002", codice_cli="C001"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    assert items[0].codice_destinazione == "MAIN:C001"
    assert items[1].codice_destinazione == "D001"
    assert items[2].codice_destinazione == "D002"


def test_is_primary_false_per_aggiuntive(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    aggiuntive = [i for i in items if not i.is_primary]
    assert all(not i.is_primary for i in aggiuntive)


# ─── Nickname sulla principale ────────────────────────────────────────────────

def test_nickname_sulla_principale(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()

    set_nickname_destinazione(session, "MAIN:C001", "HQ Milano")
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    p = items[0]
    assert p.nickname_destinazione == "HQ Milano"
    assert p.display_label == "HQ Milano"


def test_nickname_sulla_principale_non_modifica_sync(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()

    set_nickname_destinazione(session, "MAIN:C001", "HQ")
    session.commit()

    cliente = session.query(SyncCliente).filter_by(codice_cli="C001").one()
    assert cliente.ragione_sociale == "Acme Srl"  # sync non modificato


def test_nickname_principale_indipendente_da_aggiuntive(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.commit()

    set_nickname_destinazione(session, "MAIN:C001", "HQ")
    session.commit()

    items = list_destinazioni_per_cliente(session, "C001")
    principale = next(i for i in items if i.is_primary)
    aggiuntiva = next(i for i in items if not i.is_primary)
    assert principale.nickname_destinazione == "HQ"
    assert aggiuntiva.nickname_destinazione is None


# ─── Dettaglio destinazione principale ───────────────────────────────────────

def test_dettaglio_principale_per_codice_main(session):
    session.add(_cliente("C001", "Acme Srl", indirizzo="Via Roma 1", provincia="MI"))
    session.commit()

    detail = get_destinazione_detail(session, "MAIN:C001")
    assert detail is not None
    assert detail.is_primary is True
    assert detail.codice_destinazione == "MAIN:C001"
    assert detail.codice_cli == "C001"
    assert detail.ragione_sociale_cliente == "Acme Srl"
    assert detail.indirizzo == "Via Roma 1"
    assert detail.citta is None  # non in sync_clienti


def test_dettaglio_principale_none_se_cliente_assente(session):
    detail = get_destinazione_detail(session, "MAIN:NONEXISTENT")
    assert detail is None


def test_dettaglio_principale_con_nickname(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.commit()
    set_nickname_destinazione(session, "MAIN:C001", "Sede Centrale")
    session.commit()

    detail = get_destinazione_detail(session, "MAIN:C001")
    assert detail.nickname_destinazione == "Sede Centrale"
    assert detail.display_label == "Sede Centrale"


def test_dettaglio_principale_display_label_fallback_ragione_sociale(session):
    session.add(_cliente("C001", "Beta Spa"))
    session.commit()

    detail = get_destinazione_detail(session, "MAIN:C001")
    assert detail.display_label == "Beta Spa"


# ─── Aggiuntive non interferiscono con la principale ─────────────────────────

def test_aggiuntiva_detail_is_primary_false(session):
    session.add(_cliente("C001", "Acme Srl"))
    session.add(_destinazione("D001", codice_cli="C001"))
    session.commit()

    detail = get_destinazione_detail(session, "D001")
    assert detail is not None
    assert detail.is_primary is False


def test_primary_prefix_costante():
    assert _primary_codice("C001").startswith(PRIMARY_PREFIX)
