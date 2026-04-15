"""
Test del Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029).

Copertura:
- is_negative_stock: logica pura
  - inventory_qty < 0 -> True
  - inventory_qty == 0 -> False
  - inventory_qty > 0 -> False
  - None -> False
- list_warnings_v1: query + read model con SQLite in-memory
  - articolo con stock negativo -> genera NEGATIVE_STOCK
  - articolo con stock positivo -> nessun warning
  - articolo con stock zero -> nessun warning
  - articolo non attivo in sync_articoli -> nessun warning (fuori perimetro)
  - articolo non presente in sync_articoli -> nessun warning
  - piu articoli negativi -> un warning per articolo (no duplicati)
  - warning_id unico per articolo
  - campi shape canonica verificati
  - anomaly_qty = abs(stock_calculated)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.warnings import is_invalid_stock_capacity, is_missing_raw_bar_length, is_negative_stock, list_warnings_v1

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
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _art(session, codice_articolo, attivo=True):
    session.add(SyncArticolo(
        codice_articolo=codice_articolo,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _avail(session, article_code, inventory_qty, set_aside_qty=Decimal("0"), committed_qty=Decimal("0")):
    availability_qty = inventory_qty - set_aside_qty - committed_qty
    session.add(CoreAvailability(
        article_code=article_code,
        inventory_qty=inventory_qty,
        customer_set_aside_qty=set_aside_qty,
        committed_qty=committed_qty,
        availability_qty=availability_qty,
        computed_at=_NOW,
    ))
    session.flush()


# ─── Logica pura ──────────────────────────────────────────────────────────────

def test_is_negative_stock_negativo():
    assert is_negative_stock(Decimal("-1")) is True


def test_is_negative_stock_molto_negativo():
    assert is_negative_stock(Decimal("-200.5")) is True


def test_is_negative_stock_zero():
    assert is_negative_stock(Decimal("0")) is False


def test_is_negative_stock_positivo():
    assert is_negative_stock(Decimal("25")) is False


def test_is_negative_stock_none():
    assert is_negative_stock(None) is False


# ─── Query: NEGATIVE_STOCK generato ──────────────────────────────────────────

def test_stock_negativo_genera_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    w = warnings[0]
    assert w.type == "NEGATIVE_STOCK"
    assert w.entity_type == "article"
    assert w.entity_key == "ART001"
    assert w.article_code == "ART001"
    assert w.stock_calculated == Decimal("-10")
    assert w.anomaly_qty == Decimal("10")
    assert w.warning_id == "NEGATIVE_STOCK:ART001"
    assert w.source_module == "warnings"
    assert "produzione" in w.visible_to_areas
    assert w.severity == "warning"
    # SQLite restituisce datetime naive — confronto senza timezone
    assert w.created_at.replace(tzinfo=None) == _NOW.replace(tzinfo=None)


def test_anomaly_qty_e_abs_stock(session):
    """anomaly_qty = abs(stock_calculated)."""
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-37.5"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    assert warnings[0].anomaly_qty == Decimal("37.5")
    assert warnings[0].stock_calculated == Decimal("-37.5")


# ─── Query: nessun warning ────────────────────────────────────────────────────

def test_stock_positivo_nessun_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("25"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_stock_zero_nessun_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("0"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_articolo_non_attivo_nessun_warning(session):
    """Articolo fuori perimetro operativo (attivo=False) non genera warning."""
    _art(session, "ART001", attivo=False)
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_articolo_non_in_sync_nessun_warning(session):
    """Stock negativo senza corrispondente in sync_articoli non genera warning."""
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_tabella_vuota_nessun_warning(session):
    assert list_warnings_v1(session) == []


# ─── Query: piu articoli, no duplicati ────────────────────────────────────────

def test_piu_articoli_un_warning_ciascuno(session):
    """Ogni articolo con stock negativo genera esattamente un warning."""
    _art(session, "ART001")
    _art(session, "ART002")
    _art(session, "ART003")
    _avail(session, "ART001", Decimal("-5"))
    _avail(session, "ART002", Decimal("10"))
    _avail(session, "ART003", Decimal("-20"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 2
    codes = {w.article_code for w in warnings}
    assert codes == {"ART001", "ART003"}


def test_warning_id_unici(session):
    """warning_id distinto per ogni articolo — nessun duplicato."""
    _art(session, "ART001")
    _art(session, "ART002")
    _avail(session, "ART001", Decimal("-5"))
    _avail(session, "ART002", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)
    ids = [w.warning_id for w in warnings]

    assert len(ids) == len(set(ids))
    assert set(ids) == {"NEGATIVE_STOCK:ART001", "NEGATIVE_STOCK:ART002"}


def test_ordinamento_peggiori_prima(session):
    """Stock piu negativo appare prima nell'ordinamento."""
    _art(session, "ART001")
    _art(session, "ART002")
    _avail(session, "ART001", Decimal("-3"))
    _avail(session, "ART002", Decimal("-20"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 2
    assert warnings[0].article_code == "ART002"  # -20 < -3
    assert warnings[1].article_code == "ART001"


def test_mix_attivi_e_non_attivi(session):
    """Solo articoli attivi generano warning, anche con stock negativo gli inattivi no."""
    _art(session, "ATTIVO")
    _art(session, "INATTIVO", attivo=False)
    _avail(session, "ATTIVO", Decimal("-5"))
    _avail(session, "INATTIVO", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    assert warnings[0].article_code == "ATTIVO"


# ─── Logica pura: is_invalid_stock_capacity (TASK-V2-091) ────────────────────

def test_is_invalid_stock_capacity_none():
    assert is_invalid_stock_capacity(None) is True


def test_is_invalid_stock_capacity_zero():
    assert is_invalid_stock_capacity(Decimal("0")) is True


def test_is_invalid_stock_capacity_negativa():
    """Capacity negativa (edge case override errato) e comunque invalida."""
    assert is_invalid_stock_capacity(Decimal("-1")) is True


def test_is_invalid_stock_capacity_valida():
    assert is_invalid_stock_capacity(Decimal("50")) is False


def test_is_invalid_stock_capacity_piccola_positiva():
    """Anche un valore piccolo ma > 0 e valido."""
    assert is_invalid_stock_capacity(Decimal("0.001")) is False


# ─── Helpers per INVALID_STOCK_CAPACITY integration tests ────────────────────

_CAPACITY_PARAMS_W = {"max_container_weight_kg": 25}
_TEST_PARAMS_W = {
    "windows_months": [3],
    "percentile": 50,
    "zscore_threshold": 0.0,
    "min_nonzero_months": 1,
    "min_movements": 0,
}

_w_id_seq = 0


def _next_w_id():
    global _w_id_seq
    _w_id_seq += 1
    return _w_id_seq


@pytest.fixture(autouse=True)
def reset_w_id_seq():
    global _w_id_seq
    _w_id_seq = 0


def _config_stock(session, capacity_params=None):
    from nssp_v2.core.stock_policy.config import set_stock_logic_config
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params=_TEST_PARAMS_W,
        capacity_logic_params=capacity_params if capacity_params is not None else _CAPACITY_PARAMS_W,
    )
    session.flush()


def _famiglia_w(session, code="FAM1", aggrega=True, gestione_scorte_attiva=True):
    session.add(ArticoloFamiglia(
        code=code,
        label=code,
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=aggrega,
        gestione_scorte_attiva=gestione_scorte_attiva,
    ))
    session.flush()


def _art_w(session, codice="ART001", contenitori=None, peso_grammi=None):
    session.add(SyncArticolo(
        codice_articolo=codice,
        attivo=True,
        contenitori_magazzino=contenitori,
        peso_grammi=peso_grammi,
        synced_at=_NOW,
    ))
    session.flush()


def _config_art_w(session, codice="ART001", famiglia_code="FAM1", capacity_override=None):
    session.add(CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        capacity_override_qty=capacity_override,
        updated_at=_NOW,
    ))
    session.flush()


def _movimento_w(session, codice="ART001", scaricata=10.0):
    session.add(SyncMagReale(
        id_movimento=_next_w_id(),
        codice_articolo=codice,
        quantita_scaricata=scaricata,
        data_movimento=datetime(2026, 3, 15),
        synced_at=_NOW,
    ))
    session.flush()


# ─── Query: INVALID_STOCK_CAPACITY generato ──────────────────────────────────

def test_invalid_capacity_genera_warning(session):
    """Articolo by_article senza contenitori/peso → capacity None → warning."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    _art_w(session, contenitori=None)  # capacity_calculated = None
    _config_art_w(session)
    session.commit()

    warnings = list_warnings_v1(session)

    cap_warnings = [w for w in warnings if w.type == "INVALID_STOCK_CAPACITY"]
    assert len(cap_warnings) == 1
    w = cap_warnings[0]
    assert w.article_code == "ART001"
    assert w.warning_id == "INVALID_STOCK_CAPACITY:ART001"
    assert w.entity_type == "article"
    assert w.entity_key == "ART001"
    assert w.source_module == "warnings"
    assert w.severity == "warning"
    assert w.capacity_calculated_qty is None
    assert w.capacity_override_qty is None
    assert w.capacity_effective_qty is None
    assert "produzione" in w.visible_to_areas
    assert "magazzino" in w.visible_to_areas
    assert "admin" in w.visible_to_areas


def test_invalid_capacity_senza_peso_genera_warning(session):
    """Articolo con contenitori ma senza peso_grammi → capacity None → warning."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    _art_w(session, contenitori="2", peso_grammi=None)
    _config_art_w(session)
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert len(cap_warnings) == 1
    assert cap_warnings[0].capacity_calculated_qty is None


def test_capacity_valida_nessun_warning(session):
    """Articolo by_article con contenitori + peso + config → capacity valida → nessun warning."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    # capacity = 25 * 2 / (500/1000) = 100
    _art_w(session, contenitori="2", peso_grammi=Decimal("500"))
    _config_art_w(session)
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert cap_warnings == []


def test_capacity_override_valido_nessun_warning(session):
    """Articolo con capacity_override_qty > 0 → capacity effettiva valida → nessun warning."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    _art_w(session, contenitori=None)  # calculated = None
    _config_art_w(session, capacity_override=Decimal("100"))  # override vince
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert cap_warnings == []


def test_articolo_non_by_article_nessun_warning(session):
    """Articolo con aggrega=False (by_customer_order_line) escluso dal perimetro stock."""
    _config_stock(session)
    _famiglia_w(session, aggrega=False)
    _art_w(session, contenitori=None)
    _config_art_w(session)
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert cap_warnings == []


def test_invalid_capacity_warning_id_unico(session):
    """Ogni articolo genera al massimo un INVALID_STOCK_CAPACITY warning."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    _art_w(session, codice="ART001", contenitori=None)
    _art_w(session, codice="ART002", contenitori=None)
    _config_art_w(session, codice="ART001")
    _config_art_w(session, codice="ART002")
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert len(cap_warnings) == 2
    ids = {w.warning_id for w in cap_warnings}
    assert ids == {"INVALID_STOCK_CAPACITY:ART001", "INVALID_STOCK_CAPACITY:ART002"}


def test_invalid_capacity_stock_fields_none(session):
    """INVALID_STOCK_CAPACITY non popola stock_calculated/anomaly_qty (campi NEGATIVE_STOCK)."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    _art_w(session, contenitori=None)
    _config_art_w(session)
    session.commit()

    cap_warnings = [w for w in list_warnings_v1(session) if w.type == "INVALID_STOCK_CAPACITY"]
    assert len(cap_warnings) == 1
    w = cap_warnings[0]
    assert w.stock_calculated is None
    assert w.anomaly_qty is None


def test_entrambi_i_tipi_warning_coesistono(session):
    """NEGATIVE_STOCK e INVALID_STOCK_CAPACITY coesistono nella stessa lista."""
    _config_stock(session)
    _famiglia_w(session, aggrega=True)
    # Articolo by_article senza capacity → INVALID_STOCK_CAPACITY
    _art_w(session, codice="ART001", contenitori=None)
    _config_art_w(session, codice="ART001")
    # Stesso articolo con stock negativo → NEGATIVE_STOCK
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    all_warnings = list_warnings_v1(session)
    types = {w.type for w in all_warnings}
    assert "NEGATIVE_STOCK" in types
    assert "INVALID_STOCK_CAPACITY" in types


# ─── Logica pura: is_missing_raw_bar_length (TASK-V2-122) ────────────────────

def test_is_missing_raw_bar_length_none():
    assert is_missing_raw_bar_length(None) is True


def test_is_missing_raw_bar_length_zero():
    assert is_missing_raw_bar_length(Decimal("0")) is True


def test_is_missing_raw_bar_length_negativo():
    assert is_missing_raw_bar_length(Decimal("-1")) is True


def test_is_missing_raw_bar_length_valido():
    assert is_missing_raw_bar_length(Decimal("3000")) is False


def test_is_missing_raw_bar_length_piccolo_positivo():
    assert is_missing_raw_bar_length(Decimal("0.001")) is False


# ─── Helpers per MISSING_RAW_BAR_LENGTH integration tests ─────────────────────

def _famiglia_bar(session, code="BARRE", raw_bar_length_mm_enabled=True):
    session.add(ArticoloFamiglia(
        code=code,
        label=code.capitalize(),
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=True,
        gestione_scorte_attiva=False,
        raw_bar_length_mm_enabled=raw_bar_length_mm_enabled,
    ))
    session.flush()


def _art_bar(session, codice="ART001"):
    session.add(SyncArticolo(
        codice_articolo=codice,
        attivo=True,
        synced_at=_NOW,
    ))
    session.flush()


def _config_bar(session, codice="ART001", famiglia_code="BARRE", raw_bar_length_mm=None):
    session.add(CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        raw_bar_length_mm=raw_bar_length_mm,
        updated_at=_NOW,
    ))
    session.flush()


# ─── Query: MISSING_RAW_BAR_LENGTH generato ──────────────────────────────────

def test_missing_bar_genera_warning_quando_valore_assente(session):
    """Famiglia con raw_bar_length_mm_enabled=True, articolo senza raw_bar_length_mm → warning."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=None)
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert len(warnings) == 1
    w = warnings[0]
    assert w.article_code == "ART001"
    assert w.warning_id == "MISSING_RAW_BAR_LENGTH:ART001"
    assert w.entity_type == "article"
    assert w.entity_key == "ART001"
    assert w.source_module == "warnings"
    assert w.severity == "warning"
    assert w.famiglia_code == "BARRE"
    assert w.raw_bar_length_mm_enabled is True
    assert w.raw_bar_length_mm is None


def test_missing_bar_genera_warning_quando_valore_zero(session):
    """raw_bar_length_mm = 0 e non valido → warning."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=Decimal("0"))
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert len(warnings) == 1
    assert warnings[0].raw_bar_length_mm == Decimal("0")


def test_missing_bar_nessun_warning_quando_valore_valido(session):
    """Articolo con raw_bar_length_mm > 0 → nessun warning."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=Decimal("3000"))
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert warnings == []


def test_missing_bar_nessun_warning_quando_flag_disabilitato(session):
    """Famiglia con raw_bar_length_mm_enabled=False → nessun warning anche senza valore."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=False)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=None)
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert warnings == []


def test_missing_bar_audience_corretta(session):
    """visible_to_areas default include produzione e admin."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=None)
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert len(warnings) == 1
    areas = warnings[0].visible_to_areas
    assert "produzione" in areas
    assert "admin" in areas


def test_missing_bar_piu_articoli(session):
    """Piu articoli nella stessa famiglia con flag abilitato → un warning per articolo."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _art_bar(session, "ART002")
    _art_bar(session, "ART003")
    _config_bar(session, "ART001", raw_bar_length_mm=None)       # → warning
    _config_bar(session, "ART002", raw_bar_length_mm=Decimal("3000"))  # → nessun warning
    _config_bar(session, "ART003", raw_bar_length_mm=Decimal("0"))     # → warning
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert len(warnings) == 2
    codes = {w.article_code for w in warnings}
    assert codes == {"ART001", "ART003"}


def test_missing_bar_warning_id_unici(session):
    """warning_id distinto per ogni articolo."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _art_bar(session, "ART002")
    _config_bar(session, "ART001", raw_bar_length_mm=None)
    _config_bar(session, "ART002", raw_bar_length_mm=None)
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    ids = {w.warning_id for w in warnings}
    assert ids == {"MISSING_RAW_BAR_LENGTH:ART001", "MISSING_RAW_BAR_LENGTH:ART002"}


def test_missing_bar_non_popola_campi_stock(session):
    """MISSING_RAW_BAR_LENGTH non popola stock_calculated/anomaly_qty/capacity_*."""
    _famiglia_bar(session, raw_bar_length_mm_enabled=True)
    _art_bar(session, "ART001")
    _config_bar(session, "ART001", raw_bar_length_mm=None)
    session.commit()

    warnings = [w for w in list_warnings_v1(session) if w.type == "MISSING_RAW_BAR_LENGTH"]
    assert len(warnings) == 1
    w = warnings[0]
    assert w.stock_calculated is None
    assert w.anomaly_qty is None
    assert w.capacity_effective_qty is None


def test_tutti_i_tipi_warning_coesistono(session):
    """NEGATIVE_STOCK, INVALID_STOCK_CAPACITY e MISSING_RAW_BAR_LENGTH coesistono."""
    _config_stock(session)
    _famiglia_w(session, code="FAM1", aggrega=True)
    _famiglia_bar(session, code="BARRE", raw_bar_length_mm_enabled=True)
    # ART001: stock negativo → NEGATIVE_STOCK; by_article senza capacity → INVALID_STOCK_CAPACITY
    _art_w(session, codice="ART001", contenitori=None)
    _config_art_w(session, codice="ART001", famiglia_code="FAM1")
    _avail(session, "ART001", Decimal("-5"))
    # ART002: barra mancante → MISSING_RAW_BAR_LENGTH
    _art_bar(session, "ART002")
    _config_bar(session, "ART002", famiglia_code="BARRE", raw_bar_length_mm=None)
    session.commit()

    all_warnings = list_warnings_v1(session)
    types = {w.type for w in all_warnings}
    assert "NEGATIVE_STOCK" in types
    assert "INVALID_STOCK_CAPACITY" in types
    assert "MISSING_RAW_BAR_LENGTH" in types
