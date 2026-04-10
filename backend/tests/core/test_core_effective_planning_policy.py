"""
Test del Core effective planning policy articoli (TASK-V2-064, DL-ARCH-V2-026).

Copertura:
- resolve_planning_policy: funzione pura centralizzata
  - override esplicito True/False prevale sul default famiglia
  - override None eredita il default famiglia
  - override None senza famiglia -> None (valore indefinito)
- list_articoli: effective policy esposta in ArticoloItem
- get_articolo_detail: effective policy esposta in ArticoloDetail
- casi boundary: solo override, solo famiglia, entrambi, nessuno dei due
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import (
    get_articolo_detail,
    list_articoli,
    resolve_planning_policy,
)
from nssp_v2.sync.articoli.models import SyncArticolo

# Importati per Base.metadata.create_all
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

def _art(session, codice, attivo=True):
    session.add(SyncArticolo(
        codice_articolo=codice,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _famiglia(session, code, considera=False, aggrega=False, is_active=True):
    f = ArticoloFamiglia(
        code=code,
        label=f"Famiglia {code}",
        is_active=is_active,
        considera_in_produzione=considera,
        aggrega_codice_in_produzione=aggrega,
    )
    session.add(f)
    session.flush()
    return f


def _config(session, codice, famiglia_code=None, override_considera=None, override_aggrega=None):
    c = CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        updated_at=_NOW,
        override_considera_in_produzione=override_considera,
        override_aggrega_codice_in_produzione=override_aggrega,
    )
    session.add(c)
    session.flush()
    return c


# ─── Test resolve_planning_policy (funzione pura) ─────────────────────────────

class TestResolvePlanningPolicy:

    def test_override_true_prevale_su_default_false(self):
        assert resolve_planning_policy(True, False) is True

    def test_override_false_prevale_su_default_true(self):
        assert resolve_planning_policy(False, True) is False

    def test_override_true_prevale_su_default_true(self):
        assert resolve_planning_policy(True, True) is True

    def test_override_false_prevale_su_default_false(self):
        assert resolve_planning_policy(False, False) is False

    def test_override_none_eredita_default_true(self):
        assert resolve_planning_policy(None, True) is True

    def test_override_none_eredita_default_false(self):
        assert resolve_planning_policy(None, False) is False

    def test_override_none_senza_famiglia_none(self):
        """Nessun override e nessuna famiglia: valore indefinito."""
        assert resolve_planning_policy(None, None) is None

    def test_override_true_senza_famiglia(self):
        """Override esplicito senza famiglia: l'override vale comunque."""
        assert resolve_planning_policy(True, None) is True

    def test_override_false_senza_famiglia(self):
        """Override esplicito False senza famiglia: l'override vale comunque."""
        assert resolve_planning_policy(False, None) is False


# ─── Test list_articoli: effective policy in ArticoloItem ────────────────────

class TestListArticoliEffectivePolicy:

    def test_articolo_senza_config_ne_famiglia(self, session):
        """Nessuna config e nessuna famiglia: effective policy = None."""
        _art(session, "ART001")

        result = list_articoli(session)
        assert len(result) == 1
        assert result[0].effective_considera_in_produzione is None
        assert result[0].effective_aggrega_codice_in_produzione is None

    def test_articolo_con_famiglia_eredita_default(self, session):
        """Articolo con famiglia e nessun override: eredita i default famiglia."""
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=False)
        _config(session, "ART001", famiglia_code="FAM")

        result = list_articoli(session)
        assert len(result) == 1
        assert result[0].effective_considera_in_produzione is True
        assert result[0].effective_aggrega_codice_in_produzione is False

    def test_override_considera_true_prevale_su_default_false(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=False, aggrega=False)
        _config(session, "ART001", famiglia_code="FAM", override_considera=True)

        result = list_articoli(session)
        assert len(result) == 1
        assert result[0].effective_considera_in_produzione is True
        assert result[0].effective_aggrega_codice_in_produzione is False  # eredita

    def test_override_aggrega_false_prevale_su_default_true(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=True)
        _config(session, "ART001", famiglia_code="FAM", override_aggrega=False)

        result = list_articoli(session)
        assert len(result) == 1
        assert result[0].effective_considera_in_produzione is True   # eredita
        assert result[0].effective_aggrega_codice_in_produzione is False  # override

    def test_entrambi_gli_override_impostati(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=True)
        _config(session, "ART001", famiglia_code="FAM",
                override_considera=False, override_aggrega=False)

        result = list_articoli(session)
        assert len(result) == 1
        assert result[0].effective_considera_in_produzione is False
        assert result[0].effective_aggrega_codice_in_produzione is False

    def test_due_articoli_policy_diverse(self, session):
        """Due articoli con policy diverse nella stessa sessione."""
        _art(session, "ART001")
        _art(session, "ART002")
        _famiglia(session, "FAM", considera=True, aggrega=False)
        _config(session, "ART001", famiglia_code="FAM")
        _config(session, "ART002", famiglia_code="FAM", override_considera=False)

        result = list_articoli(session)
        by_code = {r.codice_articolo: r for r in result}

        assert by_code["ART001"].effective_considera_in_produzione is True   # eredita
        assert by_code["ART002"].effective_considera_in_produzione is False  # override


# ─── Test get_articolo_detail: effective policy in ArticoloDetail ─────────────

class TestGetArticoloDetailEffectivePolicy:

    def test_articolo_senza_config_ne_famiglia(self, session):
        """Nessuna config: effective policy = None."""
        _art(session, "ART001")

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is None
        assert detail.effective_aggrega_codice_in_produzione is None

    def test_articolo_con_famiglia_eredita_default(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=True)
        _config(session, "ART001", famiglia_code="FAM")

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is True
        assert detail.effective_aggrega_codice_in_produzione is True

    def test_override_considera_false_prevale_su_default_true(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=False)
        _config(session, "ART001", famiglia_code="FAM", override_considera=False)

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is False
        assert detail.effective_aggrega_codice_in_produzione is False  # eredita default

    def test_override_aggrega_true_prevale_su_default_false(self, session):
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=False, aggrega=False)
        _config(session, "ART001", famiglia_code="FAM", override_aggrega=True)

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is False  # eredita
        assert detail.effective_aggrega_codice_in_produzione is True  # override

    def test_override_senza_famiglia(self, session):
        """Override esplicito su articolo senza famiglia assegnata."""
        _art(session, "ART001")
        _config(session, "ART001", famiglia_code=None,
                override_considera=True, override_aggrega=False)

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is True
        assert detail.effective_aggrega_codice_in_produzione is False

    def test_famiglia_non_attiva_non_risolve_policy(self, session):
        """Articolo con famiglia inattiva: la famiglia non appare nella mappa attive
        quindi effective policy = None (come senza famiglia)."""
        _art(session, "ART001")
        _famiglia(session, "FAM", considera=True, aggrega=True, is_active=False)
        _config(session, "ART001", famiglia_code="FAM")

        detail = get_articolo_detail(session, "ART001")
        assert detail is not None
        assert detail.effective_considera_in_produzione is None
        assert detail.effective_aggrega_codice_in_produzione is None
