"""
Logiche pure stock policy V1 (TASK-V2-084, TASK-V2-087, TASK-V2-088, DL-ARCH-V2-030).

Funzioni pure — nessun accesso al DB, nessun side effect.
Ogni funzione e testabile in isolamento.

Strategy mensile (TASK-V2-087/088 — algoritmo riallineato al profilo V1):
  monthly_stock_base_from_sales_v1:
    Stima della quantita mensile media di consumo con finestre multiple,
    filtro outlier (z-score) e percentile configurabile.

    Params configurabili (da core_stock_logic_config.monthly_base_params_json):
      windows_months      — lista di finestre di lookback (default: [12, 6, 3])
      percentile          — percentile da applicare ai consumi mensili (default: 50)
      zscore_threshold    — soglia z-score per filtrare outlier (default: 2.0)
      min_nonzero_months  — minimo mesi con consumo > 0 per validare la finestra (default: 1)
      min_movements       — soglia globale minima righe movimento nel periodo (default: 0 = disabilitato)
      rounding_scale      — cifre decimali del risultato finale (default: None = nessun arrotondamento)

    Algoritmo:
      0. Se total_movements < min_movements (e min_movements > 0) → None
      1. Per ogni finestra W in windows_months:
         a. Prende gli ultimi W mesi (zero per mesi senza movimenti)
         b. Filtra outlier con |z-score| > zscore_threshold (solo se len >= 3)
         c. Verifica che ci siano almeno min_nonzero_months mesi con consumo > 0
         d. Calcola il percentile sulla distribuzione filtrata
      2. Media le stime di finestra valide
      3. None se nessuna finestra produce una stima valida
      4. Se rounding_scale e configurato, arrotonda il risultato

    Fallback None (TASK-V2-088 — decisione esplicita):
      La funzione restituisce None (non 0) quando:
      - non ci sono dati (monthly_sales vuoto o min_movements non soddisfatto)
      - nessuna finestra produce una stima valida (min_nonzero_months non soddisfatto)
      None segnala "dati insufficienti" — distinto da Decimal("0") che segnala
      "consumo reale = zero". Il layer chiamante tratta None come "incalcolabile".

Logica capacity fissa (TASK-V2-092 — formula legacy riallineata):
  capacity_from_containers_v1:
    capacity_calculated_qty = max_container_weight_kg * containers / article_weight_kg
    containers = ART_CONTEN (intero | decimale | a/b)
    article_weight_kg = peso_grammi / 1000
    max_container_weight_kg da capacity_logic_params["max_container_weight_kg"]
    Fallback None se ART_CONTEN / peso_grammi / max_container_weight_kg non validi.

Formule finali (DL-ARCH-V2-030 §5):
  target_stock_qty = min(capacity_effective_qty, effective_stock_months * monthly_stock_base_qty)
  trigger_stock_qty = effective_stock_trigger_months * monthly_stock_base_qty
  capacity_effective_qty = capacity_override_qty if override else capacity_calculated_qty
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation


# ─── Helper: timeline mensile ─────────────────────────────────────────────────

def _build_month_sequence(num_months: int, reference_date: datetime | None = None) -> list[tuple[int, int]]:
    """Genera sequenza di (anno, mese) degli ultimi N mesi (dal piu recente).

    Args:
        num_months: numero di mesi da generare
        reference_date: data di riferimento (default: datetime.now())

    Returns:
        lista di (anno, mese), dal mese piu recente al piu lontano
    """
    ref = reference_date or datetime.now()
    months = []
    year, month = ref.year, ref.month
    for _ in range(num_months):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


# ─── Helper: z-score outlier filter ──────────────────────────────────────────

def _filter_outliers_zscore(values: list[Decimal], threshold: float) -> list[Decimal]:
    """Rimuove valori con |z-score| > threshold.

    Non filtra se:
    - meno di 3 valori (campione troppo piccolo)
    - threshold <= 0 (filtro disabilitato)
    - deviazione standard == 0 (tutti i valori identici)
    """
    if len(values) < 3 or threshold <= 0:
        return list(values)
    n = Decimal(len(values))
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    if variance == 0:
        return list(values)
    std = variance.sqrt()
    thr = Decimal(str(threshold))
    return [v for v in values if abs(v - mean) / std <= thr]


# ─── Helper: percentile interpolato ──────────────────────────────────────────

def _compute_percentile(values: list[Decimal], percentile: int) -> Decimal:
    """Calcola il percentile con interpolazione lineare.

    Args:
        values: lista di valori (non vuota)
        percentile: 0-100

    Returns:
        valore al percentile richiesto
    """
    if not values:
        return Decimal("0")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    # Indice reale (0-based)
    idx = Decimal(str(percentile)) / Decimal("100") * Decimal(str(n - 1))
    lower = int(idx)
    upper = lower + 1
    if upper >= n:
        return sorted_vals[lower]
    frac = idx - Decimal(lower)
    return sorted_vals[lower] + frac * (sorted_vals[upper] - sorted_vals[lower])


# ─── Strategy: monthly_stock_base_from_sales_v1 ───────────────────────────────

def estimate_monthly_stock_base_from_sales_v1(
    monthly_sales: dict[tuple[int, int], Decimal],
    params: dict,
    reference_date: datetime | None = None,
    total_movements: int = 0,
) -> Decimal | None:
    """Strategy `monthly_stock_base_from_sales_v1` con finestre multiple.

    Stima la quantita mensile media di consumo usando finestre di lookback
    multiple, filtro outlier z-score e percentile configurabile.

    Args:
        monthly_sales: mappa {(anno, mese): total_scaricata} — solo mesi con movimenti
        params: parametri configurabili (da core_stock_logic_config.monthly_base_params_json):
            - windows_months (list[int]): finestre di lookback (default [12, 6, 3])
            - percentile (int): percentile 0-100 (default 50)
            - zscore_threshold (float): soglia z-score outlier (default 2.0)
            - min_nonzero_months (int): minimo mesi con consumo > 0 (default 1)
            - min_movements (int): soglia globale righe movimento (default 0 = disabilitato)
            - rounding_scale (int | None): cifre decimali risultato (default None = nessun arrotondamento)
        reference_date: data di riferimento per la timeline (default: datetime.now())
        total_movements: numero totale righe movimento nel periodo di lookback

    Returns:
        stima mensile media come Decimal, oppure None se dati insufficienti
        (None = "incalcolabile", distinto da Decimal("0") = "consumo reale zero")
    """
    windows_months: list[int] = [int(w) for w in params.get("windows_months", [12, 6, 3])]
    percentile: int = int(params.get("percentile", 50))
    zscore_threshold: float = float(params.get("zscore_threshold", 2.0))
    min_nonzero_months: int = int(params.get("min_nonzero_months", 1))
    min_movements: int = int(params.get("min_movements", 0))
    rounding_scale_raw = params.get("rounding_scale", None)
    rounding_scale: int | None = int(rounding_scale_raw) if rounding_scale_raw is not None else None

    if not windows_months:
        return None

    # Soglia globale movimenti (TASK-V2-088)
    if min_movements > 0 and total_movements < min_movements:
        return None

    max_window = max(windows_months)
    month_sequence = _build_month_sequence(max_window, reference_date)

    estimates: list[Decimal] = []
    for w in windows_months:
        window_months = month_sequence[:w]
        values = [monthly_sales.get(ym, Decimal("0")) for ym in window_months]

        # Filtro outlier
        filtered = _filter_outliers_zscore(values, zscore_threshold)

        # Soglia minima mesi con consumo
        nonzero_count = sum(1 for v in filtered if v > Decimal("0"))
        if nonzero_count < min_nonzero_months:
            continue

        estimate = _compute_percentile(filtered, percentile)
        estimates.append(estimate)

    if not estimates:
        return None

    result = sum(estimates) / Decimal(len(estimates))

    # Arrotondamento opzionale (TASK-V2-088)
    if rounding_scale is not None:
        from decimal import ROUND_HALF_UP
        quantizer = Decimal("0." + "0" * rounding_scale) if rounding_scale > 0 else Decimal("1")
        result = result.quantize(quantizer, rounding=ROUND_HALF_UP)

    return result


# ─── Strategy: monthly_stock_base_weighted_v2 ────────────────────────────────

def estimate_monthly_stock_base_weighted_v2(
    monthly_sales: dict[tuple[int, int], Decimal],
    params: dict,
    reference_date: datetime | None = None,
    total_movements: int = 0,
) -> Decimal | None:
    """Strategy `monthly_stock_base_weighted_v2` — come v1 ma con pesi per finestra.

    Identica a v1 nella struttura (multi-finestra, z-score, percentile), ma invece
    di mediare le stime delle finestre con peso uniforme usa pesi configurabili.
    Di default le finestre piu recenti pesano di piu, cosi i trend recenti
    influenzano la stima piu di quanto facciano in v1.

    Params configurabili (stessi di v1 piu):
        windows_months      — lista di finestre di lookback (default: [12, 6, 3])
        window_weights      — pesi per ogni finestra (default: [1, 2, 3])
                              deve avere la stessa lunghezza di windows_months
                              le finestre che non superano la validazione non
                              contribuiscono ne alla somma pesata ne al denominatore
        percentile          — percentile da applicare (default: 50)
        zscore_threshold    — soglia z-score outlier (default: 2.0)
        min_nonzero_months  — minimo mesi con consumo > 0 per validare finestra (default: 1)
        min_movements       — soglia globale righe movimento (default: 0 = disabilitato)
        rounding_scale      — cifre decimali risultato (default: None)

    Algoritmo:
        0. Se total_movements < min_movements (e min_movements > 0) → None
        1. Per ogni finestra W (con peso associato):
           a. Prende gli ultimi W mesi (zero per mesi senza movimenti)
           b. Filtra outlier con z-score
           c. Verifica min_nonzero_months
           d. Calcola il percentile sulla distribuzione filtrata
        2. Risultato = sum(stima_i * peso_i) / sum(pesi_validi)
        3. None se nessuna finestra valida

    Differenza rispetto a v1:
        v1  → media semplice (ogni finestra vale uguale)
        v2  → media pesata (finestre recenti valgono di piu per default)
    """
    windows_months: list[int] = [int(w) for w in params.get("windows_months", [12, 6, 3])]
    percentile: int = int(params.get("percentile", 50))
    zscore_threshold: float = float(params.get("zscore_threshold", 2.0))
    min_nonzero_months: int = int(params.get("min_nonzero_months", 1))
    min_movements: int = int(params.get("min_movements", 0))
    rounding_scale_raw = params.get("rounding_scale", None)
    rounding_scale: int | None = int(rounding_scale_raw) if rounding_scale_raw is not None else None

    # Pesi: default crescente verso le finestre piu recenti
    raw_weights = params.get("window_weights", list(range(1, len(windows_months) + 1)))
    window_weights: list[Decimal] = [Decimal(str(w)) for w in raw_weights]

    # Allinea lunghezza pesi a windows_months (tronca o estende con 1)
    if len(window_weights) < len(windows_months):
        window_weights += [Decimal("1")] * (len(windows_months) - len(window_weights))
    else:
        window_weights = window_weights[: len(windows_months)]

    if not windows_months:
        return None

    if min_movements > 0 and total_movements < min_movements:
        return None

    max_window = max(windows_months)
    month_sequence = _build_month_sequence(max_window, reference_date)

    weighted_sum = Decimal("0")
    weight_total = Decimal("0")

    for w, weight in zip(windows_months, window_weights):
        window_months = month_sequence[:w]
        values = [monthly_sales.get(ym, Decimal("0")) for ym in window_months]

        filtered = _filter_outliers_zscore(values, zscore_threshold)

        nonzero_count = sum(1 for v in filtered if v > Decimal("0"))
        if nonzero_count < min_nonzero_months:
            continue

        estimate = _compute_percentile(filtered, percentile)
        weighted_sum += estimate * weight
        weight_total += weight

    if weight_total == Decimal("0"):
        return None

    result = weighted_sum / weight_total

    if rounding_scale is not None:
        from decimal import ROUND_HALF_UP
        quantizer = Decimal("0." + "0" * rounding_scale) if rounding_scale > 0 else Decimal("1")
        result = result.quantize(quantizer, rounding=ROUND_HALF_UP)

    return result


# ─── Strategy: monthly_stock_base_segmented_v1 ───────────────────────────────

def estimate_monthly_stock_base_segmented_v1(
    monthly_sales: dict[tuple[int, int], Decimal],
    params: dict,
    reference_date: datetime | None = None,
    total_movements: int = 0,
) -> Decimal | None:
    """Strategy `monthly_stock_base_segmented_v1` — stima adattiva per segmento domanda.

    Classifica ogni articolo in base alla continuita della domanda nel periodo
    di lookback e applica una formula diversa per ciascun segmento:

      CONTINUO  (active_months >= continuous_threshold):
        Usa il percentile configurato sui valori mensili (con zero-fill OK perche
        la domanda e genuinamente mensile). Rileva trend confrontando la media
        degli ultimi 3 mesi con la media del periodo intero e seleziona la finestra
        piu adatta: 3m se trend crescente, 6m se decrescente, full se stabile.

      REGOLARE  (active_months >= regular_threshold, < continuous_threshold):
        Usa total_qty / lookback_months * regular_factor.
        Non risente del zero-fill: stima quanto viene venduto in media al mese
        tenendo conto dei periodi di inattivita come parte del normale ciclo.

      INTERMITTENTE (active_months >= 1, < regular_threshold):
        Usa total_qty / lookback_months * intermittent_factor.
        Stima minima basata sul throughput totale senza margine aggiuntivo.

      DORMANTE (active_months == 0):
        Restituisce None — nessun dato recente su cui basarsi.

    Params configurabili (da core_stock_logic_config.monthly_base_params_json):
      lookback_months         — mesi di lookback totale (default: 12)
      continuous_threshold    — soglia mesi per "continuo" (default: 8)
      regular_threshold       — soglia mesi per "regolare" (default: 3)
      percentile_continuous   — percentile per articoli continui (default: 70)
      zscore_threshold        — soglia outlier z-score per continui (default: 2.0)
      regular_factor          — moltiplicatore per regolari (default: 1.2)
      intermittent_factor     — moltiplicatore per intermittenti (default: 1.0)
      trend_ratio_threshold   — soglia ratio 3m/full per rilevare trend (default: 1.5)
      min_movements           — soglia globale righe movimento (default: 3)
      rounding_scale          — cifre decimali risultato (default: None)

    Differenza rispetto a v1/v2:
      v1/v2  — stessa formula per tutti, basata su percentile di valori mensili
               con zero-fill. Penalizza gli articoli a rotazione bassa.
      segmented — formula diversa per segmento. Gli articoli intermittenti usano
               il throughput totale (non il percentile), evitando la distorsione
               da zero-fill.
    """
    lookback_months: int = int(params.get("lookback_months", 12))
    continuous_threshold: int = int(params.get("continuous_threshold", 8))
    regular_threshold: int = int(params.get("regular_threshold", 3))
    percentile_continuous: int = int(params.get("percentile_continuous", 70))
    zscore_threshold: float = float(params.get("zscore_threshold", 2.0))
    regular_factor: Decimal = Decimal(str(params.get("regular_factor", 1.2)))
    intermittent_factor: Decimal = Decimal(str(params.get("intermittent_factor", 1.0)))
    trend_ratio_threshold: float = float(params.get("trend_ratio_threshold", 1.5))
    min_movements: int = int(params.get("min_movements", 3))
    rounding_scale_raw = params.get("rounding_scale", None)
    rounding_scale: int | None = int(rounding_scale_raw) if rounding_scale_raw is not None else None

    if min_movements > 0 and total_movements < min_movements:
        return None

    month_seq = _build_month_sequence(lookback_months, reference_date)
    values_full = [monthly_sales.get(ym, Decimal("0")) for ym in month_seq]

    active_months = sum(1 for v in values_full if v > Decimal("0"))

    # Dormante
    if active_months == 0:
        return None

    # ── Continuo: percentile su finestra adattiva (rilevamento trend) ──────────
    if active_months >= continuous_threshold:
        # Confronta media 3m vs media periodo intero per rilevare trend
        values_3m = [monthly_sales.get(ym, Decimal("0")) for ym in month_seq[:3]]
        mean_3m = sum(values_3m) / Decimal("3")
        mean_full = sum(values_full) / Decimal(str(lookback_months))

        if mean_full > Decimal("0"):
            trend_ratio = float(mean_3m / mean_full)
        else:
            trend_ratio = 1.0

        if trend_ratio > trend_ratio_threshold:
            # Trend crescente — usa finestra recente 3m
            window_values = values_3m
        elif trend_ratio < 1.0 / trend_ratio_threshold:
            # Trend decrescente — usa finestra intermedia 6m
            window_values = [monthly_sales.get(ym, Decimal("0")) for ym in month_seq[:6]]
        else:
            # Stabile — usa periodo intero
            window_values = values_full

        filtered = _filter_outliers_zscore(window_values, zscore_threshold)
        result = _compute_percentile(filtered, percentile_continuous)

    # ── Regolare / Intermittente: throughput mensile ────────────────────────────
    else:
        total_qty = sum(v for v in values_full if v > Decimal("0"))
        base = total_qty / Decimal(str(lookback_months))
        if active_months >= regular_threshold:
            result = base * regular_factor
        else:
            result = base * intermittent_factor

    if result <= Decimal("0"):
        return None

    if rounding_scale is not None:
        from decimal import ROUND_HALF_UP
        quantizer = Decimal("0." + "0" * rounding_scale) if rounding_scale > 0 else Decimal("1")
        result = result.quantize(quantizer, rounding=ROUND_HALF_UP)

    return result


# ─── Logica fissa: capacity_from_containers_v1 ───────────────────────────────

def _parse_contenitori(raw: str | None) -> Decimal | None:
    """Parsa ART_CONTEN nelle forme: intero, decimale, frazionaria a/b.

    Returns:
        Decimal > 0 se il parsing e riuscito, None altrimenti.
    """
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    # Forma frazionaria a/b
    if '/' in s:
        parts = s.split('/', 1)
        try:
            num = Decimal(parts[0].strip())
            den = Decimal(parts[1].strip())
        except (InvalidOperation, ValueError):
            return None
        if den == Decimal("0"):
            return None
        value = num / den
    else:
        try:
            value = Decimal(s)
        except (InvalidOperation, ValueError):
            return None
    return value if value > Decimal("0") else None


def estimate_capacity_from_containers_v1(
    contenitori_magazzino: str | None,
    peso_grammi: Decimal | None,
    params: dict,
) -> Decimal | None:
    """Logica fissa `capacity_from_containers_v1` — formula legacy V1 (TASK-V2-092).

    Formula:
        capacity_calculated_qty = max_container_weight_kg * containers / article_weight_kg

    Dove:
        containers          = ART_CONTEN parsato (intero, decimale, o frazione a/b)
        article_weight_kg   = peso_grammi / 1000
        max_container_weight_kg = params["max_container_weight_kg"]

    Fallback None se:
        - ART_CONTEN non presente / non parseable / <= 0
        - peso_grammi None / zero / <= 0
        - max_container_weight_kg non in params

    Args:
        contenitori_magazzino: valore grezzo ART_CONTEN (stringa o None)
        peso_grammi: peso articolo in grammi (ART_KG nel mirror V2) — None se assente
        params: parametri della logica capacity (da core_stock_logic_config.capacity_logic_params_json)

    Returns:
        capacity calcolata come Decimal, oppure None se dati insufficienti
    """
    containers = _parse_contenitori(contenitori_magazzino)
    if containers is None:
        return None

    if peso_grammi is None or peso_grammi <= Decimal("0"):
        return None

    max_kg_raw = params.get("max_container_weight_kg")
    if max_kg_raw is None:
        return None
    try:
        max_kg = Decimal(str(max_kg_raw))
    except (InvalidOperation, ValueError):
        return None
    if max_kg <= Decimal("0"):
        return None

    article_weight_kg = peso_grammi / Decimal("1000")
    return max_kg * containers / article_weight_kg


# ─── Risoluzione capacity effective ──────────────────────────────────────────

def resolve_capacity_effective(
    capacity_calculated: Decimal | None,
    capacity_override: Decimal | None,
) -> Decimal | None:
    """Risolve capacity_effective_qty (DL-ARCH-V2-030 §2, TASK-V2-083).

    Regola:
    - capacity_override_qty vince se presente (anche se zero)
    - altrimenti usa capacity_calculated_qty

    Returns:
        capacity effettiva, oppure None se nessun valore disponibile
    """
    if capacity_override is not None:
        return capacity_override
    return capacity_calculated


# ─── Formule finali ───────────────────────────────────────────────────────────

def compute_target_stock_qty(
    capacity_effective: Decimal | None,
    effective_stock_months: Decimal | None,
    monthly_stock_base: Decimal | None,
) -> Decimal | None:
    """Calcola target_stock_qty (DL-ARCH-V2-030 §5).

    Formula:
        target = min(capacity_effective, effective_stock_months * monthly_stock_base)

    Tutti e tre gli operandi devono essere not None per produrre un risultato.
    Se capacity_effective e None il min non e applicabile:
        target = effective_stock_months * monthly_stock_base
    """
    if effective_stock_months is None or monthly_stock_base is None:
        return None
    raw = effective_stock_months * monthly_stock_base
    if capacity_effective is None:
        return raw
    return min(capacity_effective, raw)


def compute_trigger_stock_qty(
    effective_stock_trigger_months: Decimal | None,
    monthly_stock_base: Decimal | None,
) -> Decimal | None:
    """Calcola trigger_stock_qty (DL-ARCH-V2-030 §5).

    Formula:
        trigger = effective_stock_trigger_months * monthly_stock_base

    Entrambi gli operandi devono essere not None per produrre un risultato.
    """
    if effective_stock_trigger_months is None or monthly_stock_base is None:
        return None
    return effective_stock_trigger_months * monthly_stock_base
