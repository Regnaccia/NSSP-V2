"""
Test di integrazione per la gestione del catalogo famiglie articolo (TASK-V2-026).

Verificano:
- creazione nuova famiglia
- validazioni create (code duplicato, label vuota, code vuoto)
- toggle is_active (attiva → inattiva → attiva)
- n_articoli corretto nel risultato di toggle
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import (
    create_famiglia,
    toggle_famiglia_active,
    toggle_famiglia_considera_produzione,
    list_famiglie_catalog,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


# ─── create_famiglia ──────────────────────────────────────────────────────────

def test_create_famiglia_inserisce(session):
    row = create_famiglia(session, "test_fam", "Test Famiglia")
    session.commit()
    assert row.code == "test_fam"
    assert row.label == "Test Famiglia"
    assert row.is_active is True
    assert row.n_articoli == 0


def test_create_famiglia_sort_order(session):
    row = create_famiglia(session, "fam_ord", "Con ordine", sort_order=10)
    session.commit()
    assert row.sort_order == 10


def test_create_famiglia_persiste_in_db(session):
    create_famiglia(session, "fam_db", "Persiste")
    session.commit()
    obj = session.query(ArticoloFamiglia).filter_by(code="fam_db").one()
    assert obj.label == "Persiste"
    assert obj.is_active is True


def test_create_famiglia_code_duplicato_raises(session):
    create_famiglia(session, "dup", "Prima")
    session.commit()
    with pytest.raises(ValueError, match="già esistente"):
        create_famiglia(session, "dup", "Seconda")


def test_create_famiglia_label_vuota_raises(session):
    with pytest.raises(ValueError, match="label"):
        create_famiglia(session, "ok_code", "")


def test_create_famiglia_code_vuoto_raises(session):
    with pytest.raises(ValueError, match="codice"):
        create_famiglia(session, "  ", "Label ok")


def test_create_famiglia_code_trimmed(session):
    row = create_famiglia(session, "  trimmed  ", "Label")
    session.commit()
    assert row.code == "trimmed"


# ─── toggle_famiglia_active ───────────────────────────────────────────────────

def test_toggle_disattiva_famiglia_attiva(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True))
    session.commit()

    row = toggle_famiglia_active(session, "fam1")
    session.commit()
    assert row.is_active is False


def test_toggle_riattiva_famiglia_inattiva(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=False))
    session.commit()

    row = toggle_famiglia_active(session, "fam1")
    session.commit()
    assert row.is_active is True


def test_toggle_idempotente_doppio(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True))
    session.commit()

    toggle_famiglia_active(session, "fam1")
    session.commit()
    row = toggle_famiglia_active(session, "fam1")
    session.commit()
    assert row.is_active is True


def test_toggle_non_trovato_raises(session):
    with pytest.raises(ValueError, match="non trovata"):
        toggle_famiglia_active(session, "inesistente")


def test_toggle_restituisce_n_articoli(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True))
    session.add(CoreArticoloConfig(codice_articolo="ART001", famiglia_code="fam1",
                                   updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)))
    session.add(CoreArticoloConfig(codice_articolo="ART002", famiglia_code="fam1",
                                   updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)))
    session.commit()

    row = toggle_famiglia_active(session, "fam1")
    session.commit()
    assert row.n_articoli == 2


# ─── list_famiglie_catalog dopo operazioni ────────────────────────────────────

def test_catalog_include_famiglia_creata(session):
    create_famiglia(session, "nuova", "Nuova Famiglia")
    session.commit()
    catalog = list_famiglie_catalog(session)
    codes = {f.code for f in catalog}
    assert "nuova" in codes


def test_catalog_mostra_famiglia_inattiva(session):
    session.add(ArticoloFamiglia(code="inattiva", label="Inattiva", is_active=False))
    session.commit()
    catalog = list_famiglie_catalog(session)
    codes = {f.code for f in catalog}
    assert "inattiva" in codes


# ─── toggle_famiglia_considera_produzione ─────────────────────────────────────

def test_considera_produzione_default_false(session):
    create_famiglia(session, "fam1", "Fam 1")
    session.commit()
    obj = session.query(ArticoloFamiglia).filter_by(code="fam1").one()
    assert obj.considera_in_produzione is False


def test_toggle_considera_produzione_attiva(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True, considera_in_produzione=False))
    session.commit()
    row = toggle_famiglia_considera_produzione(session, "fam1")
    session.commit()
    assert row.considera_in_produzione is True


def test_toggle_considera_produzione_disattiva(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True, considera_in_produzione=True))
    session.commit()
    row = toggle_famiglia_considera_produzione(session, "fam1")
    session.commit()
    assert row.considera_in_produzione is False


def test_toggle_considera_produzione_doppio_idempotente(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True, considera_in_produzione=False))
    session.commit()
    toggle_famiglia_considera_produzione(session, "fam1")
    session.commit()
    row = toggle_famiglia_considera_produzione(session, "fam1")
    session.commit()
    assert row.considera_in_produzione is False


def test_toggle_considera_produzione_non_trovata_raises(session):
    with pytest.raises(ValueError, match="non trovata"):
        toggle_famiglia_considera_produzione(session, "inesistente")


def test_catalog_espone_considera_in_produzione(session):
    session.add(ArticoloFamiglia(code="fam1", label="Fam 1", is_active=True, considera_in_produzione=True))
    session.add(ArticoloFamiglia(code="fam2", label="Fam 2", is_active=True, considera_in_produzione=False))
    session.commit()
    catalog = {f.code: f for f in list_famiglie_catalog(session)}
    assert catalog["fam1"].considera_in_produzione is True
    assert catalog["fam2"].considera_in_produzione is False
