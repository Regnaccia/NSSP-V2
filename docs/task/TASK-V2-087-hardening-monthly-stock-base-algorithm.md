# TASK-V2-087 - Hardening monthly stock base algorithm

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
- `docs/task/TASK-V2-084-core-stock-policy-metrics-v1.md`

## Goal

Riallineare l'algoritmo reale di `monthly_stock_base_qty` al profilo V1 ragionato, prima di
integrare la stock policy in `Planning Candidates`.

## Context

`TASK-V2-084` ha introdotto un primo slice funzionante di stock metrics, ma l'algoritmo reale
di `monthly_stock_base_from_sales_v1` e oggi piu semplice del profilo V1 documentale:

- usa una sola finestra di lookback
- usa `total_scaricata / lookback_months`
- non applica ancora:
  - finestre multiple `12 / 6 / 3`
  - percentile configurabile
  - filtro outlier
  - soglia minima movimenti

Prima di lanciare `TASK-V2-085` serve decidere se accettare quella semplificazione oppure
riallinearla al profilo V1 piu robusto.

Questo task assume che la scelta sia: riallineare l'algoritmo.

## Scope

- aggiornare `monthly_stock_base_from_sales_v1` per usare dati da `sync_mag_reale`
  aggregati per mese
- introdurre supporto parametrico a:
  - `windows_months`
  - `percentile`
  - `zscore_threshold`
  - `min_movements`
  - eventuale `min_nonzero_months`
- calcolare la base mensile usando il profilo V1 concordato:
  - finestre multiple
  - percentile sui consumi mensili
  - media dei risultati di finestra
- mantenere:
  - `strategy_key`
  - `params_snapshot`
  - registry chiuso delle strategy
- aggiornare test Core stock metrics e logica pura

## Out of Scope

- nuove strategy oltre `monthly_stock_base_from_sales_v1`
- modifica di `capacity_from_containers_v1`
- integrazione in `Planning Candidates`
- UI/admin per tuning dei parametri

## Constraints

- nessuna lettura diretta da Easy
- dati sorgente da mirror `sync_mag_reale`
- nessun hardcode dei parametri numerici nel codice applicativo
- mantenere compatibilita col modello di configurazione introdotto in `TASK-V2-086`

## Acceptance Criteria

- `monthly_stock_base_from_sales_v1` implementa il profilo V1 documentato
- i parametri chiave dell'algoritmo sono letti da configurazione
- esistono test che coprono:
  - finestre multiple
  - percentile
  - outlier filtering
  - storico insufficiente
- `TASK-V2-085` puo partire senza gap semantici aperti sul calcolo stock

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base ai test backend aggiornati.

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**`core/stock_policy/logic.py`** — algoritmo V1 riallineato al profilo documentale:

Nuovi helper puri (no DB, no side effect):
- `_build_month_sequence(num_months, reference_date)` — timeline (anno, mese) dal piu recente; `reference_date` opzionale per testabilita
- `_filter_outliers_zscore(values, threshold)` — rimuove valori con |z| > threshold; no filtro se len < 3, threshold == 0, o deviazione standard == 0
- `_compute_percentile(values, percentile)` — interpolazione lineare 0-100

`estimate_monthly_stock_base_from_sales_v1` — firma cambiata:
```python
def estimate_monthly_stock_base_from_sales_v1(
    monthly_sales: dict[tuple[int, int], Decimal],  # {(year, month): total}
    params: dict,
    reference_date: datetime | None = None,
) -> Decimal | None
```

Params configurabili letti da `core_stock_logic_config.monthly_base_params_json`:
- `windows_months` (default `[12, 6, 3]`)
- `percentile` (default `50`)
- `zscore_threshold` (default `2.0`)
- `min_nonzero_months` (default `1`)

Algoritmo: per ogni finestra W → prende ultimi W mesi (zero per mesi senza movimenti) → filtra outlier z-score → verifica `min_nonzero_months` → calcola percentile → media delle stime valide.

**`core/stock_policy/queries.py`** — aggregazione cambiata da `SUM per articolo` a `SUM per articolo + mese`:
- `GROUP BY article, YEAR(data_movimento), MONTH(data_movimento)`
- `sales_map: dict[str, dict[tuple[int,int], Decimal]]`
- `cutoff_dt = _months_ago(max(windows_months))`
- Chiamata aggiornata: `estimate_monthly_stock_base_from_sales_v1(monthly_sales, params)`

**Test** — 72 test totali (tutti verdi):
- `test_core_stock_policy_logic.py`: aggiunto `_build_month_sequence`, `_filter_outliers_zscore`, `_compute_percentile`; aggiornato `estimate_monthly_stock_base_from_sales_v1`; mantiene tutti i test su capacity, target, trigger
- `test_core_stock_policy_metrics.py`: aggiornato helper `_config_stock_logic`, fixtures date e movimenti

**Verifiche comandi**:
```
python -m pytest tests/core/test_core_stock_policy_logic.py tests/core/test_core_stock_policy_metrics.py -v
# 72 passed
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

