# TASK-V2-090 - Admin stock logic config

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
- `docs/task/TASK-V2-086-stock-logic-config-and-strategy-selection.md`
- `docs/task/TASK-V2-087-hardening-monthly-stock-base-algorithm.md`
- `docs/task/TASK-V2-088-stock-policy-final-alignment-before-planning.md`

## Goal

Introdurre nella surface `admin` la configurazione delle logiche stock V1, con focus su:

- strategy attiva di `monthly_stock_base_qty`
- parametri configurabili della strategy
- parametri della logic fissa `capacity_from_containers_v1`

## Context

La configurazione delle logiche stock esiste gia lato Core, ma oggi non e governabile da una
surface di governo. Questa configurazione influenza il comportamento del sistema in modo
trasversale:

- metriche stock
- candidate planning
- future production proposals

Per questo la sua sede corretta e `admin`, non la vista `Planning`.

## Scope

- aggiungere nella surface `admin` una sezione o pagina dedicata alle logiche stock
- mostrare:
  - `monthly_base_strategy_key`
  - `monthly_base_params`
  - `capacity_logic_key`
  - `capacity_logic_params`
- permettere la modifica dei parametri configurabili di:
  - `monthly_stock_base_from_sales_v1`
  - `capacity_from_containers_v1`
- chiarire in UI che:
  - `monthly_base_strategy_key` e selezionabile solo tra strategie supportate
  - `capacity_logic_key` e fisso / non switchabile
- supportare almeno i parametri V1 attesi:
  - `windows_months`
  - `percentile`
  - `zscore_threshold`
  - `min_movements`
  - `min_nonzero_months`
  - `rounding_scale`
  - parametri capacity della logic fissa

## Refresh / Sync Behavior

- La surface `admin` non introduce un refresh semantico backend nuovo
- Dopo il salvataggio della configurazione, la UI deve mostrare lo stato aggiornato della config
- Eventuali ricalcoli planning/stock restano gestiti dai refresh semantici gia esistenti delle surface operative

## Out of Scope

- configurazione della stock policy famiglia/articolo
- integrazione stock-driven in `Planning Candidates`
- modal o configurazione editabile nella vista `Planning`
- badge warning

## Constraints

- nessuna logica di calcolo lato frontend
- `capacity_logic_key` deve restare visibile ma non modificabile
- la UI deve riflettere fedelmente il contratto Core di `TASK-V2-086`
- la surface `Planning` deve consumare i risultati, non governare le logiche di sistema

## Acceptance Criteria

- la surface `admin` espone una configurazione dedicata delle logiche stock
- la UI mostra strategy e parametri attivi
- i parametri V1 sono modificabili dove consentito
- `capacity_from_containers_v1` risulta chiaramente non switchabile
- la configurazione delle logiche stock non e piu prevista nella vista `Planning`

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```
python -m pytest tests/ -v
# 830 passed
```

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Nuovi endpoint admin (`app/api/admin.py`):**
- `GET /api/admin/stock-logic/config` → `StockLogicConfigResponse` (include `known_strategies` per il dropdown)
- `PUT /api/admin/stock-logic/config` body: `monthly_base_strategy_key`, `monthly_base_params`, `capacity_logic_params`
- Riusa `get_stock_logic_config` e `set_stock_logic_config` dal Core (TASK-V2-086)
- `StockLogicConfigResponse` estende `StockLogicConfig` + aggiunge `known_strategies: list[str]`
- `capacity_logic_key` restituito ma non modificabile — sempre `capacity_from_containers_v1`

**Frontend `AdminHome.tsx` — nuovo componente `StockLogicConfigSection`:**
- Sezione "Logiche stock V1" in fondo alla surface admin
- Strategy selector: dropdown popolato da `known_strategies` (evita hardcoding nel frontend)
- Parametri V1 strutturati (solo per `monthly_stock_base_from_sales_v1`):
  - `windows_months`: input testo (comma-separated), es. `12,6,3`
  - `percentile`: numero 0–100
  - `zscore_threshold`: float
  - `min_movements`: intero (0 = disabilitato)
  - `min_nonzero_months`: intero
  - `rounding_scale`: intero opzionale (vuoto = nessun arrotondamento)
- Capacity logic: riquadro read-only con key + badge "Fisso" + spiegazione non-switchabilità
- Badge "Default di sistema" quando `is_default=true`
- `buildParams()`: costruisce il dict params filtrando i campi vuoti/NaN — non invia chiavi non specificate
- `parseWindowsMonths()`: parsa stringa CSV → `number[]`, filtra valori non validi

**Nessuna regressione:** 830 test passano.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

