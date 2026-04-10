"""
Test del modello planning policy defaults e overrides (TASK-V2-063, DL-ARCH-V2-026).

Copertura:
- ArticoloFamiglia: nuovi campi di default planning policy
  - aggrega_codice_in_produzione (default False)
  - considera_in_produzione (gia esistente, riposizionato come default planning)
- CoreArticoloConfig: nuovi override nullable tri-state
  - override_considera_in_produzione (null = eredita, True/False = sovrascrive)
  - override_aggrega_codice_in_produzione (null = eredita, True/False = sovrascrive)
- Regola di risoluzione effective policy (DL-ARCH-V2-026 §4):
    effective = override if override is not None else family_default
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig

# Importati per Base.metadata.create_all
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.availability.models import CoreAvailability  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica  # noqa: F401


_NOW = datetime.now(timezone.utc)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _famiglia(session, code, considera_in_produzione=False, aggrega_codice_in_produzione=False,
              is_active=True):
    f = ArticoloFamiglia(
        code=code,
        label=f"Famiglia {code}",
        is_active=is_active,
        considera_in_produzione=considera_in_produzione,
        aggrega_codice_in_produzione=aggrega_codice_in_produzione,
    )
    session.add(f)
    session.flush()
    return f


def _config(session, codice_articolo, famiglia_code=None,
            override_considera=None, override_aggrega=None):
    c = CoreArticoloConfig(
        codice_articolo=codice_articolo,
        famiglia_code=famiglia_code,
        updated_at=_NOW,
        override_considera_in_produzione=override_considera,
        override_aggrega_codice_in_produzione=override_aggrega,
    )
    session.add(c)
    session.flush()
    return c


# ─── Test ArticoloFamiglia: default planning policy ───────────────────────────

class TestFamigliaDefaultPolicy:

    def test_aggrega_codice_default_false(self, session):
        """aggrega_codice_in_produzione ha default False (comportamento conservativo)."""
        f = ArticoloFamiglia(
            code="FAM001",
            label="Test",
            is_active=True,
            considera_in_produzione=True,
        )
        session.add(f)
        session.flush()
        session.refresh(f)
        assert f.aggrega_codice_in_produzione is False

    def test_considera_in_produzione_default_false(self, session):
        """considera_in_produzione ha default False."""
        f = ArticoloFamiglia(
            code="FAM001",
            label="Test",
            is_active=True,
        )
        session.add(f)
        session.flush()
        session.refresh(f)
        assert f.considera_in_produzione is False

    def test_famiglia_con_entrambi_i_default_true(self, session):
        """Famiglia con entrambe le policy esplicitamente True."""
        f = _famiglia(session, "FAM001",
                      considera_in_produzione=True,
                      aggrega_codice_in_produzione=True)
        session.refresh(f)
        assert f.considera_in_produzione is True
        assert f.aggrega_codice_in_produzione is True

    def test_famiglia_con_policy_miste(self, session):
        """Famiglia con considera=True, aggrega=False (caso tipico)."""
        f = _famiglia(session, "FAM001",
                      considera_in_produzione=True,
                      aggrega_codice_in_produzione=False)
        session.refresh(f)
        assert f.considera_in_produzione is True
        assert f.aggrega_codice_in_produzione is False

    def test_due_famiglie_con_policy_diverse(self, session):
        """Due famiglie con policy distinte — i valori sono indipendenti."""
        f1 = _famiglia(session, "FAM_PROD",
                       considera_in_produzione=True,
                       aggrega_codice_in_produzione=True)
        f2 = _famiglia(session, "FAM_NO_PROD",
                       considera_in_produzione=False,
                       aggrega_codice_in_produzione=False)
        session.refresh(f1)
        session.refresh(f2)

        assert f1.considera_in_produzione is True
        assert f1.aggrega_codice_in_produzione is True
        assert f2.considera_in_produzione is False
        assert f2.aggrega_codice_in_produzione is False


# ─── Test CoreArticoloConfig: override nullable tri-state ─────────────────────

class TestArticoloConfigOverride:

    def test_override_null_di_default(self, session):
        """Gli override sono null per default — eredita dalla famiglia."""
        c = _config(session, "ART001")
        session.refresh(c)
        assert c.override_considera_in_produzione is None
        assert c.override_aggrega_codice_in_produzione is None

    def test_override_considera_true(self, session):
        """Override considera=True: sovrascrive il default famiglia."""
        c = _config(session, "ART001", override_considera=True)
        session.refresh(c)
        assert c.override_considera_in_produzione is True

    def test_override_considera_false(self, session):
        """Override considera=False: sovrascrive il default famiglia."""
        c = _config(session, "ART001", override_considera=False)
        session.refresh(c)
        assert c.override_considera_in_produzione is False

    def test_override_aggrega_true(self, session):
        """Override aggrega=True: sovrascrive il default famiglia."""
        c = _config(session, "ART001", override_aggrega=True)
        session.refresh(c)
        assert c.override_aggrega_codice_in_produzione is True

    def test_override_aggrega_false(self, session):
        """Override aggrega=False: sovrascrive il default famiglia."""
        c = _config(session, "ART001", override_aggrega=False)
        session.refresh(c)
        assert c.override_aggrega_codice_in_produzione is False

    def test_entrambi_gli_override_impostati(self, session):
        """Override espliciti per entrambe le policy."""
        c = _config(session, "ART001", override_considera=True, override_aggrega=False)
        session.refresh(c)
        assert c.override_considera_in_produzione is True
        assert c.override_aggrega_codice_in_produzione is False

    def test_override_aggiornabile(self, session):
        """Un override null puo essere impostato dopo la creazione."""
        c = _config(session, "ART001")
        assert c.override_considera_in_produzione is None

        c.override_considera_in_produzione = True
        session.flush()
        session.refresh(c)
        assert c.override_considera_in_produzione is True

    def test_override_resettabile_a_null(self, session):
        """Un override impostato puo tornare a null (eredita dalla famiglia)."""
        c = _config(session, "ART001", override_considera=True)
        assert c.override_considera_in_produzione is True

        c.override_considera_in_produzione = None
        session.flush()
        session.refresh(c)
        assert c.override_considera_in_produzione is None


# ─── Test regola di risoluzione effective policy ──────────────────────────────

def _resolve(override, family_default) -> bool:
    """Implementazione locale della regola di risoluzione DL-ARCH-V2-026 §4.

    effective = override if override is not None else family_default

    Usata nei test per verificare il comportamento atteso senza dipendere da
    un'implementazione Core dedicata (fuori scope in questo task).
    """
    return override if override is not None else family_default


class TestEffectivePolicy:

    def test_null_eredita_false_da_famiglia(self, session):
        f = _famiglia(session, "FAM", considera_in_produzione=False)
        c = _config(session, "ART001", famiglia_code="FAM", override_considera=None)
        assert _resolve(c.override_considera_in_produzione, f.considera_in_produzione) is False

    def test_null_eredita_true_da_famiglia(self, session):
        f = _famiglia(session, "FAM", considera_in_produzione=True)
        c = _config(session, "ART001", famiglia_code="FAM", override_considera=None)
        assert _resolve(c.override_considera_in_produzione, f.considera_in_produzione) is True

    def test_override_true_prevale_su_default_false(self, session):
        """Override True su famiglia con default False."""
        f = _famiglia(session, "FAM", considera_in_produzione=False)
        c = _config(session, "ART001", famiglia_code="FAM", override_considera=True)
        assert _resolve(c.override_considera_in_produzione, f.considera_in_produzione) is True

    def test_override_false_prevale_su_default_true(self, session):
        """Override False su famiglia con default True."""
        f = _famiglia(session, "FAM", considera_in_produzione=True)
        c = _config(session, "ART001", famiglia_code="FAM", override_considera=False)
        assert _resolve(c.override_considera_in_produzione, f.considera_in_produzione) is False

    def test_aggrega_null_eredita_false_da_famiglia(self, session):
        f = _famiglia(session, "FAM", aggrega_codice_in_produzione=False)
        c = _config(session, "ART001", famiglia_code="FAM", override_aggrega=None)
        assert _resolve(c.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) is False

    def test_aggrega_null_eredita_true_da_famiglia(self, session):
        f = _famiglia(session, "FAM", aggrega_codice_in_produzione=True)
        c = _config(session, "ART001", famiglia_code="FAM", override_aggrega=None)
        assert _resolve(c.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) is True

    def test_aggrega_override_true_prevale_su_default_false(self, session):
        f = _famiglia(session, "FAM", aggrega_codice_in_produzione=False)
        c = _config(session, "ART001", famiglia_code="FAM", override_aggrega=True)
        assert _resolve(c.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) is True

    def test_aggrega_override_false_prevale_su_default_true(self, session):
        f = _famiglia(session, "FAM", aggrega_codice_in_produzione=True)
        c = _config(session, "ART001", famiglia_code="FAM", override_aggrega=False)
        assert _resolve(c.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) is False

    def test_policy_indipendenti_su_stesso_articolo(self, session):
        """Le due policy sono indipendenti: override per una non impatta l'altra."""
        f = _famiglia(session, "FAM",
                      considera_in_produzione=True,
                      aggrega_codice_in_produzione=False)
        c = _config(session, "ART001", famiglia_code="FAM",
                    override_considera=None,  # eredita True
                    override_aggrega=True)    # sovrascrive a True

        eff_considera = _resolve(c.override_considera_in_produzione, f.considera_in_produzione)
        eff_aggrega = _resolve(c.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione)

        assert eff_considera is True   # eredita dalla famiglia
        assert eff_aggrega is True     # override articolo sovrascrive

    def test_articolo_senza_famiglia_usa_override_diretto(self, session):
        """Articolo senza famiglia: override ha senso solo se impostato.
        Senza famiglia e senza override, la policy e undefined a livello di modello.
        Questo test verifica che il campo override sia leggibile anche senza famiglia.
        """
        c = _config(session, "ART001", famiglia_code=None, override_considera=True)
        assert c.override_considera_in_produzione is True
