"""
Test di filter_warnings_by_areas (TASK-V2-082, DL-ARCH-V2-029).

Copertura:
- admin vede tutti i warning indipendentemente da visible_to_areas
- utente produzione vede solo warning con 'produzione' in visible_to_areas
- utente magazzino vede solo warning con 'magazzino' in visible_to_areas
- utente logistica vede solo warning con 'logistica' in visible_to_areas
- utente multi-area (es. produzione + magazzino) vede unione
- utente senza aree operative (nessun ruolo area valido) non vede nessun warning
- lista vuota rimane vuota in qualsiasi caso
- warning con visible_to_areas vuota non e visibile a nessun utente non-admin
"""

from datetime import datetime, timezone
from decimal import Decimal

from nssp_v2.core.warnings.queries import filter_warnings_by_areas
from nssp_v2.core.warnings.read_models import WarningItem

_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


def _w(article_code: str, visible_to_areas: list[str]) -> WarningItem:
    return WarningItem(
        warning_id=f"NEGATIVE_STOCK:{article_code}",
        type="NEGATIVE_STOCK",
        severity="warning",
        entity_type="article",
        entity_key=article_code,
        message=f"test {article_code}",
        source_module="warnings",
        visible_to_areas=visible_to_areas,
        created_at=_NOW,
        article_code=article_code,
        stock_calculated=Decimal("-5"),
        anomaly_qty=Decimal("5"),
    )


# ─── Admin ────────────────────────────────────────────────────────────────────

def test_admin_vede_tutti_i_warning():
    warnings = [
        _w("ART001", ["produzione"]),
        _w("ART002", ["magazzino"]),
        _w("ART003", []),
    ]
    result = filter_warnings_by_areas(warnings, user_areas=[], is_admin=True)
    assert len(result) == 3


def test_admin_vede_tutto_anche_senza_aree_operativa():
    """Admin senza ruoli operativi vede ugualmente tutto."""
    warnings = [_w("ART001", ["produzione"])]
    result = filter_warnings_by_areas(warnings, user_areas=[], is_admin=True)
    assert len(result) == 1


# ─── Utente singola area ──────────────────────────────────────────────────────

def test_produzione_vede_solo_propria_area():
    warnings = [
        _w("ART001", ["produzione"]),
        _w("ART002", ["magazzino"]),
        _w("ART003", ["logistica"]),
        _w("ART004", ["produzione", "magazzino"]),
    ]
    result = filter_warnings_by_areas(warnings, user_areas=["produzione"], is_admin=False)
    codes = {w.article_code for w in result}
    assert codes == {"ART001", "ART004"}


def test_magazzino_vede_solo_propria_area():
    warnings = [
        _w("ART001", ["produzione"]),
        _w("ART002", ["magazzino"]),
    ]
    result = filter_warnings_by_areas(warnings, user_areas=["magazzino"], is_admin=False)
    assert len(result) == 1
    assert result[0].article_code == "ART002"


def test_logistica_vede_solo_propria_area():
    warnings = [
        _w("ART001", ["produzione"]),
        _w("ART002", ["logistica"]),
    ]
    result = filter_warnings_by_areas(warnings, user_areas=["logistica"], is_admin=False)
    assert len(result) == 1
    assert result[0].article_code == "ART002"


# ─── Utente multi-area ────────────────────────────────────────────────────────

def test_multi_area_vede_unione():
    """Utente con piu ruoli operativi vede l'unione delle aree."""
    warnings = [
        _w("ART001", ["produzione"]),
        _w("ART002", ["magazzino"]),
        _w("ART003", ["logistica"]),
    ]
    result = filter_warnings_by_areas(
        warnings, user_areas=["produzione", "magazzino"], is_admin=False
    )
    codes = {w.article_code for w in result}
    assert codes == {"ART001", "ART002"}


# ─── Casi limite ──────────────────────────────────────────────────────────────

def test_nessuna_area_operativa_nessun_warning():
    """Utente senza ruoli area (es. solo ruoli speciali) non vede nessun warning."""
    warnings = [_w("ART001", ["produzione"]), _w("ART002", ["magazzino"])]
    result = filter_warnings_by_areas(warnings, user_areas=[], is_admin=False)
    assert result == []


def test_warning_visible_to_areas_vuota_non_visibile():
    """Warning con visible_to_areas=[] non e visibile a nessun utente non-admin."""
    warnings = [_w("ART001", [])]
    result = filter_warnings_by_areas(warnings, user_areas=["produzione"], is_admin=False)
    assert result == []


def test_lista_vuota_rimane_vuota_admin():
    assert filter_warnings_by_areas([], user_areas=[], is_admin=True) == []


def test_lista_vuota_rimane_vuota_non_admin():
    assert filter_warnings_by_areas([], user_areas=["produzione"], is_admin=False) == []


def test_warning_visibile_in_area_corrente():
    warnings = [_w("ART001", ["produzione", "logistica"])]
    result = filter_warnings_by_areas(warnings, user_areas=["logistica"], is_admin=False)
    assert len(result) == 1
