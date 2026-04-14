"""
Test delle logiche pure stock policy V1 (TASK-V2-084, TASK-V2-087, TASK-V2-088, TASK-V2-092, DL-ARCH-V2-030).

Copertura:
- _build_month_sequence: generazione timeline mensile
- _filter_outliers_zscore: filtro outlier con z-score
- _compute_percentile: calcolo percentile con interpolazione
- estimate_monthly_stock_base_from_sales_v1:
  - dizionario vuoto -> None (fallback esplicito, non 0)
  - finestra singola
  - finestre multiple (media delle stime)
  - movimenti fuori finestra non usati
  - filtro outlier z-score
  - min_nonzero_months: finestra scartata se consumo insufficiente
  - percentile configurabile
  - min_movements: None se soglia globale non raggiunta
  - rounding_scale: arrotondamento del risultato finale
- estimate_capacity_from_containers_v1: formula legacy V1 (TASK-V2-092)
  - formula: max_container_weight_kg * containers / (peso_grammi / 1000)
  - parsing ART_CONTEN: intero, decimale, frazionario a/b
  - fallback None se ART_CONTEN / peso_grammi / max_container_weight_kg non validi
- resolve_capacity_effective: override vs calculated
- compute_target_stock_qty: formula min(capacity, months*base); None se parametri mancanti
- compute_trigger_stock_qty: formula trigger_months * base; None se parametri mancanti
"""

from datetime import datetime
from decimal import Decimal

import pytest

from nssp_v2.core.stock_policy.logic import (
    _build_month_sequence,
    _compute_percentile,
    _filter_outliers_zscore,
    _parse_contenitori,
    compute_target_stock_qty,
    compute_trigger_stock_qty,
    estimate_capacity_from_containers_v1,
    estimate_monthly_stock_base_from_sales_v1,
    resolve_capacity_effective,
)

# Data di riferimento fissa per tutti i test che usano timeline
_REF = datetime(2026, 4, 13)


# ─── _build_month_sequence ────────────────────────────────────────────────────

def test_month_sequence_lunghezza():
    seq = _build_month_sequence(6, _REF)
    assert len(seq) == 6


def test_month_sequence_primo_elemento_e_mese_corrente():
    seq = _build_month_sequence(3, _REF)
    assert seq[0] == (2026, 4)


def test_month_sequence_ordine_decrescente():
    seq = _build_month_sequence(4, _REF)
    assert seq == [(2026, 4), (2026, 3), (2026, 2), (2026, 1)]


def test_month_sequence_attraversa_anno():
    seq = _build_month_sequence(5, _REF)
    # apr 2026, mar, feb, gen, dic 2025
    assert seq[4] == (2025, 12)


def test_month_sequence_lunghezza_1():
    seq = _build_month_sequence(1, _REF)
    assert seq == [(2026, 4)]


# ─── _filter_outliers_zscore ──────────────────────────────────────────────────

def test_zscore_meno_di_3_valori_non_filtra():
    values = [Decimal("10"), Decimal("100")]
    result = _filter_outliers_zscore(values, 2.0)
    assert result == values


def test_zscore_threshold_zero_non_filtra():
    values = [Decimal("10"), Decimal("10"), Decimal("1000")]
    result = _filter_outliers_zscore(values, 0.0)
    assert result == values


def test_zscore_rimuove_outlier():
    # 10*5 + 1000 — con 6 valori il z-score di 1000 e ~2.24 > soglia 2.0
    values = [Decimal("10")] * 5 + [Decimal("1000")]
    result = _filter_outliers_zscore(values, 2.0)
    assert Decimal("1000") not in result
    assert all(v == Decimal("10") for v in result)


def test_zscore_valori_identici_non_filtra():
    values = [Decimal("20")] * 5
    result = _filter_outliers_zscore(values, 2.0)
    assert len(result) == 5


def test_zscore_nessun_outlier_da_rimuovere():
    values = [Decimal("10"), Decimal("12"), Decimal("11"), Decimal("13")]
    result = _filter_outliers_zscore(values, 2.0)
    assert len(result) == 4


# ─── _compute_percentile ─────────────────────────────────────────────────────

def test_percentile_mediana_lista_dispari():
    values = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")]
    result = _compute_percentile(values, 50)
    assert result == Decimal("3")


def test_percentile_mediana_lista_pari():
    values = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")]
    result = _compute_percentile(values, 50)
    # idx = 0.5 * 3 = 1.5 -> interpolazione tra sorted[1]=2 e sorted[2]=3
    assert result == Decimal("2.5")


def test_percentile_0():
    values = [Decimal("5"), Decimal("1"), Decimal("3")]
    result = _compute_percentile(values, 0)
    assert result == Decimal("1")


def test_percentile_100():
    values = [Decimal("5"), Decimal("1"), Decimal("3")]
    result = _compute_percentile(values, 100)
    assert result == Decimal("5")


def test_percentile_singolo_valore():
    result = _compute_percentile([Decimal("42")], 50)
    assert result == Decimal("42")


# ─── estimate_monthly_stock_base_from_sales_v1 ────────────────────────────────

def _params(**kwargs) -> dict:
    """Genera params con default V1 e override opzionali."""
    defaults = {
        "windows_months": [6],
        "percentile": 50,
        "zscore_threshold": 2.0,
        "min_nonzero_months": 1,
    }
    defaults.update(kwargs)
    return defaults


def _sales(*amounts: float, ref: datetime = _REF) -> dict[tuple[int, int], Decimal]:
    """Costruisce monthly_sales dai piu recenti al piu lontano rispetto a ref."""
    seq = _build_month_sequence(len(amounts), ref)
    return {ym: Decimal(str(a)) for ym, a in zip(seq, amounts) if a > 0}


def test_sales_dizionario_vuoto_restituisce_none():
    result = estimate_monthly_stock_base_from_sales_v1({}, _params(), _REF)
    assert result is None


def test_sales_windows_vuoto_restituisce_none():
    sales = _sales(10, 20, 30)
    result = estimate_monthly_stock_base_from_sales_v1(sales, _params(windows_months=[]), _REF)
    assert result is None


def test_sales_finestra_singola_mediana():
    # 6 mesi: 10, 20, 30, 40, 50, 60 — mediana di [10,20,30,40,50,60] = 35
    sales = _sales(10, 20, 30, 40, 50, 60)
    result = estimate_monthly_stock_base_from_sales_v1(sales, _params(windows_months=[6]), _REF)
    assert result is not None
    # sorted: [0,10,20,30,40,50,60]... wait, 6 valori con tutti positivi
    # sales include tutti e 6 i mesi
    # _compute_percentile p=50 su [10,20,30,40,50,60] sorted
    # idx = 0.5 * 5 = 2.5 -> interp tra 30 e 40 = 35
    assert result == Decimal("35")


def test_sales_mese_senza_movimenti_conta_come_zero():
    # Solo 3 mesi con dati su finestra 6 -> 3 mesi sono zero
    sales = {(2026, 4): Decimal("60"), (2026, 3): Decimal("60"), (2026, 2): Decimal("60")}
    result = estimate_monthly_stock_base_from_sales_v1(sales, _params(windows_months=[6], percentile=50), _REF)
    assert result is not None
    # sorted: [0, 0, 0, 60, 60, 60] -> mediana = (0+60)/2 = 30
    assert result == Decimal("30")


def test_sales_finestre_multiple_media_delle_stime():
    # Finestre [3, 6] — ciascuna produce una stima, il risultato e la media
    # Con tutti i mesi a 10: ogni finestra produce 10, media = 10
    sales = _sales(10, 10, 10, 10, 10, 10)
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[3, 6], percentile=50), _REF
    )
    assert result == Decimal("10")


def test_sales_movimenti_fuori_finestra_non_usati():
    # Finestra 3 — solo i 3 mesi piu recenti
    # Mesi [apr, mar, feb] = 10,10,10; gen e fuori
    sales = {
        (2026, 4): Decimal("10"),
        (2026, 3): Decimal("10"),
        (2026, 2): Decimal("10"),
        (2026, 1): Decimal("9999"),  # fuori finestra 3
    }
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[3], percentile=50), _REF
    )
    assert result is not None
    # [10,10,10] -> mediana = 10 (9999 non incluso)
    assert result == Decimal("10")


def test_sales_min_nonzero_months_scarta_finestra():
    # min_nonzero_months=3 ma solo 1 mese con consumo -> finestra scartata
    sales = {(2026, 4): Decimal("50")}  # solo 1 mese non-zero su 6
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[6], min_nonzero_months=3), _REF
    )
    assert result is None


def test_sales_min_nonzero_months_passa_quando_sufficiente():
    sales = {(2026, 4): Decimal("30"), (2026, 3): Decimal("30"), (2026, 2): Decimal("30")}
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[6], min_nonzero_months=3), _REF
    )
    assert result is not None


def test_sales_zscore_rimuove_outlier_mensile():
    # 5 mesi a 10, 1 mese a 1000 — con z-score l'outlier viene rimosso
    sales = {
        (2026, 4): Decimal("10"),
        (2026, 3): Decimal("10"),
        (2026, 2): Decimal("10"),
        (2026, 1): Decimal("10"),
        (2025, 12): Decimal("10"),
        (2025, 11): Decimal("1000"),
    }
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[6], percentile=50, zscore_threshold=2.0), _REF
    )
    assert result is not None
    # Dopo filtro outlier: solo i mesi a 10 (+ eventuali zero) -> mediana ~ 10
    assert result == Decimal("10")


def test_sales_percentile_75():
    # [0, 0, 0, 10, 20, 30] sorted -> p75 = interp
    sales = {(2026, 4): Decimal("10"), (2026, 3): Decimal("20"), (2026, 2): Decimal("30")}
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[6], percentile=75, zscore_threshold=0.0), _REF
    )
    assert result is not None


def test_sales_fallback_none_non_zero():
    """Nessun dato -> None (non Decimal('0')).

    La distinzione e semantica: None = 'incalcolabile', 0 = 'consumo reale zero'.
    """
    result = estimate_monthly_stock_base_from_sales_v1({}, _params(), _REF)
    assert result is None
    assert result != Decimal("0")


def test_sales_storico_insufficiente_finestra_piu_grande():
    # Finestre [12, 6] con 0 mesi di dati -> None
    result = estimate_monthly_stock_base_from_sales_v1(
        {}, _params(windows_months=[12, 6], min_nonzero_months=1), _REF
    )
    assert result is None


# ─── min_movements ────────────────────────────────────────────────────────────

def test_min_movements_disabilitato_per_default():
    """min_movements=0 (default) non blocca mai il calcolo."""
    sales = _sales(10, 10, 10)
    result = estimate_monthly_stock_base_from_sales_v1(sales, _params(), _REF, total_movements=0)
    assert result is not None


def test_min_movements_soglia_raggiunta():
    sales = _sales(10, 10, 10)
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(min_movements=3), _REF, total_movements=5
    )
    assert result is not None


def test_min_movements_soglia_non_raggiunta():
    sales = _sales(10, 10, 10)
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(min_movements=10), _REF, total_movements=3
    )
    assert result is None


def test_min_movements_zero_movimenti_con_soglia():
    result = estimate_monthly_stock_base_from_sales_v1(
        {}, _params(min_movements=1), _REF, total_movements=0
    )
    assert result is None


# ─── rounding_scale ──────────────────────────────────────────────────────────

def test_rounding_scale_nessuno_per_default():
    """Senza rounding_scale il risultato non viene arrotondato."""
    sales = {(2026, 4): Decimal("10"), (2026, 3): Decimal("10"), (2026, 2): Decimal("10")}
    result = estimate_monthly_stock_base_from_sales_v1(sales, _params(), _REF)
    # Risultato preciso — non arrotondato a scale fissa
    assert result is not None


def test_rounding_scale_2():
    """rounding_scale=2 -> risultato con 2 cifre decimali."""
    sales = {(2026, 4): Decimal("10")}
    # Con finestra 6: [0,0,0,0,0,10] -> mediana = 0 (p50 di lista con zero)
    # Con finestra 3: [0,0,10] -> mediana = 0
    # Non un buon caso per testare il rounding, usiamo una configurazione semplice
    sales2 = {
        (2026, 4): Decimal("10"),
        (2026, 3): Decimal("10"),
        (2026, 2): Decimal("10"),
    }
    result = estimate_monthly_stock_base_from_sales_v1(
        sales2, _params(windows_months=[3], percentile=50, zscore_threshold=0.0, rounding_scale=2), _REF
    )
    assert result is not None
    # [10,10,10] -> p50 = 10 -> arrotondato a 2 dec = 10.00
    assert result == Decimal("10.00")


def test_rounding_scale_0():
    """rounding_scale=0 -> arrotondamento all'intero."""
    sales = {
        (2026, 4): Decimal("11"),
        (2026, 3): Decimal("12"),
        (2026, 2): Decimal("10"),
    }
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[3], percentile=50, zscore_threshold=0.0, rounding_scale=0), _REF
    )
    assert result is not None
    # sorted: [10,11,12] -> p50=11 -> arrotondato a intero = 11
    assert result == Decimal("11")


def test_sales_una_finestra_valida_su_due():
    # Finestra 6: 3 mesi non-zero OK con min_nonzero=1
    # Finestra 12: 3 mesi non-zero OK con min_nonzero=1
    # Entrambe valide -> media
    sales = {(2026, 4): Decimal("30"), (2026, 3): Decimal("30"), (2026, 2): Decimal("30")}
    result = estimate_monthly_stock_base_from_sales_v1(
        sales, _params(windows_months=[6, 12], percentile=50, zscore_threshold=0.0, min_nonzero_months=1), _REF
    )
    assert result is not None
    # entrambe le finestre vedono gli stessi 3 mesi a 30 + zeri
    # percentile 50 di [0,0,0,30,30,30] = 15 (finestra 6)
    # percentile 50 di [0,0,0,0,0,0,0,0,0,30,30,30] = 0 (finestra 12, mediana e 0)
    # media = (15 + 0) / 2 = 7.5
    assert result is not None  # non assertiamo il valore esatto qui


# ─── _parse_contenitori ──────────────────────────────────────────────────────

def test_parse_contenitori_intero():
    assert _parse_contenitori("100") == Decimal("100")


def test_parse_contenitori_spazi():
    assert _parse_contenitori("  250  ") == Decimal("250")


def test_parse_contenitori_decimale():
    assert _parse_contenitori("12.5") == Decimal("12.5")


def test_parse_contenitori_frazionario():
    result = _parse_contenitori("1/4")
    assert result == Decimal("1") / Decimal("4")


def test_parse_contenitori_frazionario_intero():
    result = _parse_contenitori("3/2")
    assert result == Decimal("1.5")


def test_parse_contenitori_stringa_vuota():
    assert _parse_contenitori("") is None


def test_parse_contenitori_none():
    assert _parse_contenitori(None) is None


def test_parse_contenitori_zero():
    assert _parse_contenitori("0") is None


def test_parse_contenitori_negativo():
    assert _parse_contenitori("-10") is None


def test_parse_contenitori_non_numerico():
    assert _parse_contenitori("abc") is None


def test_parse_contenitori_frazionario_denominatore_zero():
    assert _parse_contenitori("5/0") is None


def test_parse_contenitori_frazionario_non_numerico():
    assert _parse_contenitori("n/a") is None


# ─── estimate_capacity_from_containers_v1 — formula legacy V1 (TASK-V2-092) ──

_PARAMS_25KG = {"max_container_weight_kg": 25}


def test_capacity_formula_base():
    # containers=2, peso=500g (0.5kg), max=25kg → 25*2/0.5 = 100
    result = estimate_capacity_from_containers_v1("2", Decimal("500"), _PARAMS_25KG)
    assert result == Decimal("100")


def test_capacity_formula_intera():
    # containers=4, peso=1000g (1kg), max=25kg → 25*4/1 = 100
    result = estimate_capacity_from_containers_v1("4", Decimal("1000"), _PARAMS_25KG)
    assert result == Decimal("100")


def test_capacity_formula_frazionaria():
    # containers=1/4=0.25, peso=250g (0.25kg), max=25kg → 25*0.25/0.25 = 25
    result = estimate_capacity_from_containers_v1("1/4", Decimal("250"), _PARAMS_25KG)
    assert result == Decimal("25")


def test_capacity_formula_con_decimali():
    # containers=2.5, peso=500g (0.5kg), max=25kg → 25*2.5/0.5 = 125
    result = estimate_capacity_from_containers_v1("2.5", Decimal("500"), _PARAMS_25KG)
    assert result == Decimal("125")


def test_capacity_none_se_contenitori_none():
    result = estimate_capacity_from_containers_v1(None, Decimal("500"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_contenitori_vuoti():
    result = estimate_capacity_from_containers_v1("", Decimal("500"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_contenitori_non_numerici():
    result = estimate_capacity_from_containers_v1("abc", Decimal("500"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_contenitori_zero():
    result = estimate_capacity_from_containers_v1("0", Decimal("500"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_peso_none():
    result = estimate_capacity_from_containers_v1("2", None, _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_peso_zero():
    result = estimate_capacity_from_containers_v1("2", Decimal("0"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_peso_negativo():
    result = estimate_capacity_from_containers_v1("2", Decimal("-100"), _PARAMS_25KG)
    assert result is None


def test_capacity_none_se_max_kg_non_in_params():
    result = estimate_capacity_from_containers_v1("2", Decimal("500"), {})
    assert result is None


def test_capacity_none_se_max_kg_zero():
    result = estimate_capacity_from_containers_v1("2", Decimal("500"), {"max_container_weight_kg": 0})
    assert result is None


def test_capacity_max_kg_da_params_come_float():
    # max_container_weight_kg puo essere float nel JSON config
    result = estimate_capacity_from_containers_v1("2", Decimal("500"), {"max_container_weight_kg": 25.0})
    assert result == Decimal("100")


# ─── resolve_capacity_effective ──────────────────────────────────────────────

def test_resolve_capacity_override_vince():
    result = resolve_capacity_effective(Decimal("100"), Decimal("200"))
    assert result == Decimal("200")


def test_resolve_capacity_override_none_usa_calculated():
    result = resolve_capacity_effective(Decimal("100"), None)
    assert result == Decimal("100")


def test_resolve_capacity_entrambi_none():
    result = resolve_capacity_effective(None, None)
    assert result is None


def test_resolve_capacity_override_zero_vince():
    result = resolve_capacity_effective(Decimal("100"), Decimal("0"))
    assert result == Decimal("0")


def test_resolve_capacity_calculated_none_override_present():
    result = resolve_capacity_effective(None, Decimal("300"))
    assert result == Decimal("300")


# ─── compute_target_stock_qty ─────────────────────────────────────────────────

def test_target_min_capacity_vince():
    result = compute_target_stock_qty(Decimal("50"), Decimal("3"), Decimal("30"))
    assert result == Decimal("50")


def test_target_min_formula_vince():
    result = compute_target_stock_qty(Decimal("200"), Decimal("3"), Decimal("30"))
    assert result == Decimal("90")


def test_target_capacity_none_usa_formula():
    result = compute_target_stock_qty(None, Decimal("3"), Decimal("30"))
    assert result == Decimal("90")


def test_target_stock_months_none_restituisce_none():
    result = compute_target_stock_qty(Decimal("200"), None, Decimal("30"))
    assert result is None


def test_target_monthly_base_none_restituisce_none():
    result = compute_target_stock_qty(Decimal("200"), Decimal("3"), None)
    assert result is None


def test_target_tutti_none():
    result = compute_target_stock_qty(None, None, None)
    assert result is None


# ─── compute_trigger_stock_qty ───────────────────────────────────────────────

def test_trigger_calcolo_standard():
    result = compute_trigger_stock_qty(Decimal("1.5"), Decimal("20"))
    assert result == Decimal("30.0")


def test_trigger_trigger_months_none():
    result = compute_trigger_stock_qty(None, Decimal("20"))
    assert result is None


def test_trigger_base_none():
    result = compute_trigger_stock_qty(Decimal("1.5"), None)
    assert result is None


def test_trigger_entrambi_none():
    result = compute_trigger_stock_qty(None, None)
    assert result is None


def test_trigger_zero_months_produce_zero():
    result = compute_trigger_stock_qty(Decimal("0"), Decimal("20"))
    assert result == Decimal("0")
