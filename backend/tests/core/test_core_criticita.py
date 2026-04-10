"""
Test del Core slice `criticita articoli` (TASK-V2-055, TASK-V2-056, TASK-V2-057,
TASK-V2-059, TASK-V2-060, DL-ARCH-V2-023).

Copertura:
- is_critical_v1: logica pura su ArticleLogicContext
- list_criticita_v1: query + read model con SQLite in-memory
  - perimetro articoli: solo codici presenti e attivi in sync_articoli (TASK-V2-060)
  - perimetro operativo: solo famiglie con considera_in_produzione = True (TASK-V2-056)
  - solo articoli con availability_qty < 0
  - ordinamento crescente (i peggiori sopra)
  - arricchimento descrizione e famiglia
  - articoli non critici esclusi
  - tabella vuota -> lista vuota
  - toggle solo_in_produzione (TASK-V2-057)
  - join cross-source con UPPER() per mixed-case (TASK-V2-059)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.criticita.logic import ArticleLogicContext, is_critical_v1
from nssp_v2.core.criticita.queries import list_criticita_v1

# Importati per registrare tutti i modelli in Base.metadata prima di create_all
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
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


# ─── Helper ───────────────────────────────────────────────────────────────────

def _avail(session, article_code, inventory_qty, set_aside_qty, committed_qty, availability_qty):
    session.add(CoreAvailability(
        article_code=article_code,
        inventory_qty=Decimal(str(inventory_qty)),
        customer_set_aside_qty=Decimal(str(set_aside_qty)),
        committed_qty=Decimal(str(committed_qty)),
        availability_qty=Decimal(str(availability_qty)),
        computed_at=_NOW,
    ))
    session.flush()


def _art(session, codice_articolo, descrizione_1=None, descrizione_2=None, attivo=True):
    session.add(SyncArticolo(
        codice_articolo=codice_articolo,
        descrizione_1=descrizione_1,
        descrizione_2=descrizione_2,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _famiglia(session, code, label, considera_in_produzione=False, is_active=True):
    session.add(ArticoloFamiglia(
        code=code,
        label=label,
        is_active=is_active,
        considera_in_produzione=considera_in_produzione,
    ))
    session.flush()


def _config(session, codice_articolo, famiglia_code):
    session.add(CoreArticoloConfig(codice_articolo=codice_articolo, famiglia_code=famiglia_code, updated_at=_NOW))
    session.flush()


# ─── Test logica pura is_critical_v1 ──────────────────────────────────────────

def _ctx(availability_qty):
    return ArticleLogicContext(
        article_code="ART001",
        inventory_qty=Decimal("10"),
        customer_set_aside_qty=Decimal("0"),
        committed_qty=Decimal("0"),
        availability_qty=availability_qty,
    )


def test_is_critical_v1_negativo():
    assert is_critical_v1(_ctx(Decimal("-1"))) is True


def test_is_critical_v1_zero_non_critico():
    assert is_critical_v1(_ctx(Decimal("0"))) is False


def test_is_critical_v1_positivo_non_critico():
    assert is_critical_v1(_ctx(Decimal("5"))) is False


def test_is_critical_v1_none_restituisce_false():
    ctx = ArticleLogicContext(
        article_code="ART001",
        inventory_qty=None,
        customer_set_aside_qty=None,
        committed_qty=None,
        availability_qty=None,
    )
    assert is_critical_v1(ctx) is False


def test_is_critical_v1_molto_negativo():
    assert is_critical_v1(_ctx(Decimal("-999.99"))) is True


# ─── Test perimetro articoli (TASK-V2-060) ────────────────────────────────────

def test_perimetro_esclude_codice_assente_da_sync_articoli(session):
    """Codice con availability negativa ma assente da sync_articoli: escluso (TASK-V2-060)."""
    _avail(session, "ART001", 5, 0, 20, -15)
    # nessun _art -> escluso
    assert list_criticita_v1(session, solo_in_produzione=False) == []


def test_perimetro_esclude_codice_non_attivo(session):
    """Codice presente in sync_articoli ma attivo=False: escluso (TASK-V2-060)."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", attivo=False)
    assert list_criticita_v1(session, solo_in_produzione=False) == []


def test_perimetro_include_codice_attivo(session):
    """Codice presente e attivo: incluso se critico (TASK-V2-060)."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001")
    items = list_criticita_v1(session, solo_in_produzione=False)
    assert len(items) == 1
    assert items[0].article_code == "ART001"


def test_perimetro_mix_presente_e_assente(session):
    """Solo il codice presente e attivo compare, l'orfano no (TASK-V2-060)."""
    _avail(session, "PRESENTE", 5, 0, 20, -15)
    _avail(session, "ORFANO", 5, 0, 30, -25)
    _art(session, "PRESENTE")
    # ORFANO non ha sync_articolo

    items = list_criticita_v1(session, solo_in_produzione=False)
    codes = {i.article_code for i in items}
    assert "PRESENTE" in codes
    assert "ORFANO" not in codes


# ─── Test perimetro operativo considera_in_produzione (TASK-V2-056) ───────────

def test_list_criticita_v1_esclude_senza_famiglia(session):
    """Articoli nel perimetro articoli ma senza famiglia: esclusi con solo_in_produzione=True."""
    _avail(session, "ART001", 10, 0, 50, -40)
    _art(session, "ART001")
    # nessuna _config -> nessuna famiglia -> escluso
    assert list_criticita_v1(session) == []


def test_list_criticita_v1_esclude_famiglia_non_in_produzione(session):
    """Famiglia con considera_in_produzione=False: articolo escluso dal perimetro operativo."""
    _avail(session, "ART001", 10, 0, 50, -40)
    _art(session, "ART001")
    _famiglia(session, "barre", "Barre", considera_in_produzione=False)
    _config(session, "ART001", "barre")
    assert list_criticita_v1(session) == []


def test_list_criticita_v1_esclude_famiglia_inattiva(session):
    """Famiglia inattiva: articolo escluso dal perimetro anche se considera_in_produzione=True."""
    _avail(session, "ART001", 10, 0, 50, -40)
    _art(session, "ART001")
    _famiglia(session, "speciale", "Speciale", considera_in_produzione=True, is_active=False)
    _config(session, "ART001", "speciale")
    assert list_criticita_v1(session) == []


def test_list_criticita_v1_include_famiglia_in_produzione(session):
    """Famiglia con considera_in_produzione=True e articolo attivo: incluso."""
    _avail(session, "ART001", 10, 0, 50, -40)
    _art(session, "ART001")
    _famiglia(session, "articolo_standard", "Articolo Standard", considera_in_produzione=True)
    _config(session, "ART001", "articolo_standard")
    items = list_criticita_v1(session)
    assert len(items) == 1
    assert items[0].article_code == "ART001"


def test_list_criticita_v1_mix_perimetro(session):
    """Solo gli articoli nel perimetro produzione sono inclusi."""
    _avail(session, "KO_PROD", 5, 0, 30, -25)
    _avail(session, "KO_NOPROD", 5, 0, 30, -25)
    _art(session, "KO_PROD")
    _art(session, "KO_NOPROD")
    _famiglia(session, "prod", "In produzione", considera_in_produzione=True)
    _famiglia(session, "noprod", "Non produzione", considera_in_produzione=False)
    _config(session, "KO_PROD", "prod")
    _config(session, "KO_NOPROD", "noprod")
    items = list_criticita_v1(session)
    codes = {i.article_code for i in items}
    assert "KO_PROD" in codes
    assert "KO_NOPROD" not in codes


# ─── Test list_criticita_v1 — logica e presentazione ─────────────────────────

def test_list_criticita_v1_tabella_vuota(session):
    assert list_criticita_v1(session) == []


def test_list_criticita_v1_escludi_non_critici(session):
    _avail(session, "ART001", 100, 0, 0, 100)
    _avail(session, "ART002", 50, 10, 5, 35)
    _art(session, "ART001")
    _art(session, "ART002")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    _config(session, "ART002", "prod")
    assert list_criticita_v1(session) == []


def test_list_criticita_v1_include_articolo_critico(session):
    _avail(session, "ART001", 10, 5, 20, -15)
    _art(session, "ART001")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    items = list_criticita_v1(session)
    assert len(items) == 1
    assert items[0].article_code == "ART001"
    assert items[0].availability_qty == Decimal("-15")


def test_list_criticita_v1_ordinamento_crescente(session):
    _avail(session, "ART001", 10, 0, 15, -5)
    _avail(session, "ART002", 5, 0, 30, -25)
    _avail(session, "ART003", 20, 0, 25, -5)
    _art(session, "ART001")
    _art(session, "ART002")
    _art(session, "ART003")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    _config(session, "ART002", "prod")
    _config(session, "ART003", "prod")
    items = list_criticita_v1(session)
    avail_vals = [i.availability_qty for i in items]
    assert avail_vals == sorted(avail_vals)
    assert items[0].availability_qty == Decimal("-25")


def test_list_criticita_v1_mix_critici_e_non(session):
    _avail(session, "OK001", 100, 0, 0, 100)
    _avail(session, "KO001", 10, 0, 50, -40)
    _avail(session, "KO002", 5, 0, 20, -15)
    _art(session, "OK001")
    _art(session, "KO001")
    _art(session, "KO002")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "OK001", "prod")
    _config(session, "KO001", "prod")
    _config(session, "KO002", "prod")
    items = list_criticita_v1(session)
    codes = {i.article_code for i in items}
    assert "KO001" in codes
    assert "KO002" in codes
    assert "OK001" not in codes


def test_list_criticita_v1_arricchisce_descrizione(session):
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", descrizione_1="Vite", descrizione_2="M6")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    items = list_criticita_v1(session)
    assert len(items) == 1
    assert items[0].descrizione_1 == "Vite"
    assert items[0].descrizione_2 == "M6"
    assert items[0].display_label == "Vite M6"


def test_list_criticita_v1_display_label_solo_d1(session):
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", descrizione_1="Bullone", descrizione_2=None)
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    items = list_criticita_v1(session)
    assert items[0].display_label == "Bullone"


def test_list_criticita_v1_display_label_fallback_codice(session):
    """display_label fallback = article_code quando descrizione_1 e None."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", descrizione_1=None, descrizione_2=None)
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    items = list_criticita_v1(session)
    assert items[0].display_label == "ART001"


def test_list_criticita_v1_famiglia_code_e_label_corretti(session):
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", descrizione_1="Vite")
    _famiglia(session, "articolo_standard", "Articolo Standard", considera_in_produzione=True)
    _config(session, "ART001", "articolo_standard")
    items = list_criticita_v1(session)
    assert items[0].famiglia_code == "articolo_standard"
    assert items[0].famiglia_label == "Articolo Standard"


def test_list_criticita_v1_campi_quantitativi_corretti(session):
    _avail(session, "ART001", 10, 3, 20, -13)
    _art(session, "ART001")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")
    items = list_criticita_v1(session)
    item = items[0]
    assert item.inventory_qty == Decimal("10")
    assert item.customer_set_aside_qty == Decimal("3")
    assert item.committed_qty == Decimal("20")
    assert item.availability_qty == Decimal("-13")


# ─── Test toggle solo_in_produzione (TASK-V2-057) ─────────────────────────────

def test_toggle_false_include_senza_famiglia(session):
    """Con solo_in_produzione=False, articoli senza famiglia (ma presenti in articoli) inclusi."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001")
    items = list_criticita_v1(session, solo_in_produzione=False)
    assert len(items) == 1
    assert items[0].article_code == "ART001"
    assert items[0].famiglia_code is None
    assert items[0].famiglia_label is None


def test_toggle_false_include_famiglia_non_in_produzione(session):
    """Con solo_in_produzione=False, articoli con famiglia non-produzione sono inclusi."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001")
    _famiglia(session, "barre", "Barre", considera_in_produzione=False)
    _config(session, "ART001", "barre")
    items = list_criticita_v1(session, solo_in_produzione=False)
    assert len(items) == 1
    assert items[0].article_code == "ART001"
    assert items[0].famiglia_label == "Barre"


def test_toggle_false_include_famiglia_inattiva(session):
    """Con solo_in_produzione=False, articoli con famiglia inattiva sono inclusi."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001")
    _famiglia(session, "speciale", "Speciale", considera_in_produzione=True, is_active=False)
    _config(session, "ART001", "speciale")
    items = list_criticita_v1(session, solo_in_produzione=False)
    assert len(items) == 1
    assert items[0].article_code == "ART001"


def test_toggle_false_include_tutti_i_critici_nel_perimetro_articoli(session):
    """Con solo_in_produzione=False, tutti i critici presenti in articoli sono inclusi."""
    _avail(session, "ART_PROD", 5, 0, 20, -15)
    _avail(session, "ART_NOPROD", 5, 0, 30, -25)
    _avail(session, "ART_NOFAM", 5, 0, 10, -5)
    _avail(session, "ART_OK", 100, 0, 0, 100)
    _avail(session, "ART_ORFANO", 5, 0, 20, -10)  # no sync_articolo -> escluso
    _art(session, "ART_PROD")
    _art(session, "ART_NOPROD")
    _art(session, "ART_NOFAM")
    _art(session, "ART_OK")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _famiglia(session, "noprod", "NoProd", considera_in_produzione=False)
    _config(session, "ART_PROD", "prod")
    _config(session, "ART_NOPROD", "noprod")

    items = list_criticita_v1(session, solo_in_produzione=False)
    codes = {i.article_code for i in items}
    assert "ART_PROD" in codes
    assert "ART_NOPROD" in codes
    assert "ART_NOFAM" in codes
    assert "ART_OK" not in codes
    assert "ART_ORFANO" not in codes


def test_toggle_true_vs_false_stessa_logica_criticita(session):
    """Il toggle non cambia la formula di criticita: availability_qty >= 0 escluso in entrambi."""
    _avail(session, "ART001", 100, 0, 0, 0)    # zero: non critico
    _avail(session, "ART002", 100, 0, 0, 100)  # positivo: non critico
    _art(session, "ART001")
    _art(session, "ART002")
    assert list_criticita_v1(session, solo_in_produzione=True) == []
    assert list_criticita_v1(session, solo_in_produzione=False) == []


def test_toggle_default_e_true(session):
    """Il default di solo_in_produzione e True."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001")
    # nessuna famiglia -> escluso con default True
    assert list_criticita_v1(session) == list_criticita_v1(session, solo_in_produzione=True)


# ─── Test regressione join cross-source mixed-case (TASK-V2-059) ──────────────

def test_join_art_canonico_config_lowercase(session):
    """availability ha codice canonico, sync_articoli e core_articolo_config hanno raw lowercase.

    Con join senza UPPER() il join fallisce e la famiglia non viene trovata.
    Con il fix (UPPER sul lato raw) il join va a buon fine (TASK-V2-059).
    """
    canonical = "8X7X160"
    raw = "8x7x160"
    _avail(session, canonical, 5, 0, 20, -15)
    _art(session, raw, descrizione_1="Vite", descrizione_2="M6")
    _famiglia(session, "articolo_standard", "Articolo Standard", considera_in_produzione=True)
    _config(session, raw, "articolo_standard")

    items = list_criticita_v1(session, solo_in_produzione=True)
    assert len(items) == 1, (
        f"Bug TASK-V2-059: raw='{raw}' canonical='{canonical}' non trovato"
    )
    item = items[0]
    assert item.article_code == canonical
    assert item.famiglia_code == "articolo_standard"
    assert item.famiglia_label == "Articolo Standard"
    assert item.display_label == "Vite M6"


def test_join_art_canonico_sync_lowercase(session):
    """Descrizione arricchita correttamente con mismatch casing su sync_articoli."""
    canonical = "ART-X"
    raw = "art-x"
    _avail(session, canonical, 5, 0, 20, -15)
    _art(session, raw, descrizione_1="Articolo X")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, raw, "prod")

    items = list_criticita_v1(session)
    assert len(items) == 1
    assert items[0].article_code == canonical
    assert items[0].descrizione_1 == "Articolo X"
    assert items[0].display_label == "Articolo X"


def test_join_toggle_false_con_mismatch_casing(session):
    """Con solo_in_produzione=False e mismatch casing, la famiglia e visibile."""
    canonical = "PART-001"
    raw = "Part-001"
    _avail(session, canonical, 5, 0, 20, -15)
    _art(session, raw)
    _famiglia(session, "barre", "Barre", considera_in_produzione=False)
    _config(session, raw, "barre")

    items = list_criticita_v1(session, solo_in_produzione=False)
    assert len(items) == 1
    assert items[0].famiglia_label == "Barre"


def test_join_canonical_gia_uppercase_invariato(session):
    """Caso baseline: chiave gia canonica — comportamento invariato."""
    _avail(session, "ART001", 5, 0, 20, -15)
    _art(session, "ART001", descrizione_1="Bullone")
    _famiglia(session, "prod", "Prod", considera_in_produzione=True)
    _config(session, "ART001", "prod")

    items = list_criticita_v1(session)
    assert len(items) == 1
    assert items[0].article_code == "ART001"
    assert items[0].descrizione_1 == "Bullone"
    assert items[0].famiglia_label == "Prod"
