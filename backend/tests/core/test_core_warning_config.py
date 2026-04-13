"""
Test del Core slice `warnings` — configurazione visibilita (TASK-V2-077, TASK-V2-081, DL-ARCH-V2-029).

Copertura:
- get_visible_to_areas: default se non configurato, override da DB
- list_warning_configs: tutti i tipi noti, is_default True/False
- set_warning_config: crea nuova config, aggiorna esistente
- list_warnings_v1 integrato: visible_to_areas riflette la config DB

Vocabolario TASK-V2-081: visible_to_areas = ['magazzino', 'produzione', 'logistica']
Default NEGATIVE_STOCK: ['magazzino', 'produzione']
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.warnings import (
    KNOWN_WARNING_TYPES,
    KNOWN_AREAS,
    WarningTypeConfigItem,
    get_visible_to_areas,
    list_warning_configs,
    set_warning_config,
    list_warnings_v1,
)
from nssp_v2.core.warnings.config_model import WarningTypeConfig

# Importati per registrare tutti i modelli in Base.metadata
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


_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


def _art(session, codice_articolo, attivo=True):
    session.add(SyncArticolo(codice_articolo=codice_articolo, attivo=attivo, synced_at=_NOW))
    session.flush()


def _avail(session, article_code, inventory_qty):
    session.add(CoreAvailability(
        article_code=article_code,
        inventory_qty=inventory_qty,
        customer_set_aside_qty=Decimal("0"),
        committed_qty=Decimal("0"),
        availability_qty=inventory_qty,
        computed_at=_NOW,
    ))
    session.flush()


# ─── get_visible_to_areas ────────────────────────────────────────────────────

def test_get_visible_default_se_non_configurato(session):
    """Senza righe in DB usa il default del tipo."""
    areas = get_visible_to_areas(session, "NEGATIVE_STOCK")
    assert set(areas) == {"magazzino", "produzione"}


def test_get_visible_usa_config_db(session):
    """Con riga in DB usa quella invece del default."""
    session.add(WarningTypeConfig(
        warning_type="NEGATIVE_STOCK",
        visible_to_areas=["produzione", "logistica"],
        updated_at=_NOW,
    ))
    session.commit()

    areas = get_visible_to_areas(session, "NEGATIVE_STOCK")
    assert set(areas) == {"produzione", "logistica"}


def test_get_visible_tipo_sconosciuto_ritorna_lista_vuota(session):
    areas = get_visible_to_areas(session, "TIPO_INESISTENTE")
    assert areas == []


# ─── list_warning_configs ─────────────────────────────────────────────────────

def test_list_configs_vuoto_ritorna_tutti_i_tipi_noti_con_default(session):
    """Senza config in DB restituisce tutti i tipi noti come is_default=True."""
    configs = list_warning_configs(session)
    assert len(configs) == len(KNOWN_WARNING_TYPES)

    neg = next(c for c in configs if c.warning_type == "NEGATIVE_STOCK")
    assert neg.is_default is True
    assert set(neg.visible_to_areas) == {"magazzino", "produzione"}
    assert neg.updated_at is None


def test_list_configs_con_config_persistita(session):
    """Config persistita compare con is_default=False."""
    session.add(WarningTypeConfig(
        warning_type="NEGATIVE_STOCK",
        visible_to_areas=["logistica"],
        updated_at=_NOW,
    ))
    session.commit()

    configs = list_warning_configs(session)
    neg = next(c for c in configs if c.warning_type == "NEGATIVE_STOCK")
    assert neg.is_default is False
    assert neg.visible_to_areas == ["logistica"]
    assert neg.updated_at is not None


def test_list_configs_restituisce_warning_type_config_item(session):
    configs = list_warning_configs(session)
    for c in configs:
        assert isinstance(c, WarningTypeConfigItem)


# ─── set_warning_config ───────────────────────────────────────────────────────

def test_set_config_crea_nuova_riga(session):
    result = set_warning_config(session, "NEGATIVE_STOCK", ["magazzino", "logistica"])

    assert result.warning_type == "NEGATIVE_STOCK"
    assert set(result.visible_to_areas) == {"magazzino", "logistica"}
    assert result.is_default is False
    assert result.updated_at is not None

    # Verifica persistenza
    row = session.query(WarningTypeConfig).filter_by(warning_type="NEGATIVE_STOCK").first()
    assert row is not None
    assert set(row.visible_to_areas) == {"magazzino", "logistica"}


def test_set_config_aggiorna_riga_esistente(session):
    session.add(WarningTypeConfig(
        warning_type="NEGATIVE_STOCK",
        visible_to_areas=["produzione"],
        updated_at=_NOW,
    ))
    session.commit()

    result = set_warning_config(session, "NEGATIVE_STOCK", ["logistica"])

    assert result.visible_to_areas == ["logistica"]

    row = session.query(WarningTypeConfig).filter_by(warning_type="NEGATIVE_STOCK").first()
    assert row.visible_to_areas == ["logistica"]


def test_set_config_lista_vuota_ammessa(session):
    """Area list vuota e valida — warning non visibile in nessuna area operativa."""
    result = set_warning_config(session, "NEGATIVE_STOCK", [])
    assert result.visible_to_areas == []


# ─── Integrazione: list_warnings_v1 usa la config DB ──────────────────────────

def test_warnings_usano_areas_da_db(session):
    """list_warnings_v1 riflette la config DB in visible_to_areas."""
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-5"))
    set_warning_config(session, "NEGATIVE_STOCK", ["logistica"])
    session.commit()

    warnings = list_warnings_v1(session)
    assert len(warnings) == 1
    assert warnings[0].visible_to_areas == ["logistica"]


def test_warnings_usano_default_se_nessuna_config(session):
    """Senza config DB list_warnings_v1 usa il default ['magazzino', 'produzione']."""
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    warnings = list_warnings_v1(session)
    assert len(warnings) == 1
    assert set(warnings[0].visible_to_areas) == {"magazzino", "produzione"}


# ─── Vocabolario ──────────────────────────────────────────────────────────────

def test_known_warning_types_non_vuoto():
    assert "NEGATIVE_STOCK" in KNOWN_WARNING_TYPES


def test_known_areas_contiene_aree_attese():
    assert "magazzino" in KNOWN_AREAS
    assert "produzione" in KNOWN_AREAS
    assert "logistica" in KNOWN_AREAS
