# TASK-V2-084 - Core stock policy metrics V1

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

## Goal

Introdurre il primo computed slice Core della stock policy V1 con metriche articolo-specifiche.

## Context

Dopo:

- il modello configurativo stock di dominio
- la configurazione delle logiche stock

serve un building block Core separato che calcoli:

- `monthly_stock_base_qty`
- `capacity_calculated_qty`
- `capacity_effective_qty`
- `target_stock_qty`
- `trigger_stock_qty`

senza ancora cambiare `Planning Candidates`.

## Scope

- introdurre un computed fact o read model dedicato alle stock metrics
- includere:
  - `article_code`
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`
  - `strategy_key`
  - `params_snapshot`
  - `algorithm_key`
  - `computed_at`
- consumare la `strategy_key` e i parametri configurati per il calcolo della base mensile
- applicare la logica fissa `capacity_from_containers_v1` per `capacity_calculated_qty`
- usare:
  - `effective_stock_months`
  - `effective_stock_trigger_months`
  - `capacity_override_qty`

## Out of Scope

- configurazione della `strategy_key` o dei parametri
- integrazione in `Planning Candidates`
- UI dedicata
- UI/admin per cambiare strategy o parametri

## Constraints

- non introdurre stock policy nel ramo `by_customer_order_line`
- non creare duplicazione con `availability` o altri fact esistenti
- il calcolo della base mensile deve leggere la strategy attiva da configurazione
- `capacity_from_containers_v1` resta non switchabile
- le logiche stock leggono dai mirror `sync_*` interni e dai fact/read model Core V2
- non si leggono dati direttamente da Easy dentro il calcolo delle metriche

## Implementation Notes

- per `monthly_stock_base_from_sales_v1` la sorgente operativa e il mirror interno `sync_mag_reale`, non Easy diretto
- per `capacity_from_containers_v1` i dati articolo necessari arrivano dal mirror interno `sync_articoli` e dagli override/config interni
- il computed slice deve costruire metriche Core sopra dati gia sincronizzati e persistiti in V2

## Acceptance Criteria

- esiste un building block Core dedicato alle stock metrics V1
- `target_stock_qty` e `trigger_stock_qty` sono calcolati secondo `DL-ARCH-V2-030`
- la logica di `monthly_stock_base_qty` usa `strategy_key` e parametri configurati
- `capacity_calculated_qty` usa la logica fissa `capacity_from_containers_v1`

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base ai test backend introdotti.

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Nuovo modulo** `core/stock_policy/` esteso con:

**`logic.py`** — funzioni pure (no DB, testabili in isolamento):
- `estimate_monthly_stock_base_from_sales_v1(total_scaricata_qty, lookback_months)` → `total / months`
- `estimate_capacity_from_containers_v1(contenitori_magazzino)` → parsing `Decimal` da `ART_CONTEN`
- `resolve_capacity_effective(calculated, override)` → override vince se not None (anche override=0)
- `compute_target_stock_qty(capacity_effective, stock_months, monthly_base)` → `min(capacity, months*base)`; se `capacity is None` → `months*base`
- `compute_trigger_stock_qty(trigger_months, monthly_base)` → `trigger_months * base`

**`read_models.py`** — `StockMetricsItem` (Pydantic frozen):
- campi: `article_code`, `monthly_stock_base_qty`, `capacity_calculated_qty`, `capacity_effective_qty`, `target_stock_qty`, `trigger_stock_qty`, `strategy_key`, `params_snapshot`, `algorithm_key`, `computed_at`
- tutti i campi metriche nullable

**`queries.py`** — `list_stock_metrics_v1(session)`:
- legge `get_stock_logic_config()` per strategy + `lookback_months`
- aggrega `SUM(quantita_scaricata)` da `sync_mag_reale` per `UPPER(TRIM(codice_articolo))` nel periodo di lookback
- LEFT JOIN `sync_articoli` + `core_articolo_config` (solo articoli attivi)
- risolve effective policy da override articolo > default famiglia
- produce un `StockMetricsItem` per articolo attivo

**`__init__.py`** aggiornato con tutti gli export TASK-V2-084.

**Test** — 52 test totali (tutti verdi):
- `tests/core/test_core_stock_policy_logic.py` — 31 test puri su tutte le funzioni `logic.py`
- `tests/core/test_core_stock_policy_metrics.py` — 21 test integrazione su `list_stock_metrics_v1` con SQLite in-memory

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`
