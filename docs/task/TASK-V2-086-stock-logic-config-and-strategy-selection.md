# TASK-V2-086 - Stock logic config and strategy selection

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

Introdurre la configurazione interna delle logiche stock V1, separando:

- selezione della `strategy` per `monthly_stock_base_qty`
- parametri configurabili delle logiche stock

senza ancora calcolare le metriche finali.

## Context

Dopo `TASK-V2-083` il modello stock di dominio e disponibile, ma mancano ancora:

- una configurazione persistente per scegliere la strategy attiva di `monthly_stock_base_qty`
- parametri numerici configurabili per evitare hardcode nel codice
- la distinzione esplicita tra logiche switchable e logiche fisse di setup

Questo slice deve precedere il calcolo delle metriche Core.

## Scope

- introdurre una configurazione interna V2 per la logica `monthly_stock_base_qty`
- supportare:
  - `strategy_key`
  - `params_json`
  - eventuale metadato di attivazione/versione se utile al modello scelto
- fissare il registry supportato per `monthly_stock_base_qty`
- registrare come prima strategy disponibile:
  - `monthly_stock_base_from_sales_v1`
- introdurre parametri configurabili per la logica fissa:
  - `capacity_from_containers_v1`
- rendere i parametri leggibili dal Core stock metrics

## Out of Scope

- calcolo di `monthly_stock_base_qty`
- calcolo di `capacity_calculated_qty`
- integrazione in `Planning Candidates`
- UI/admin dedicata alla modifica della configurazione

## Constraints

- `monthly_stock_base_qty` deve usare una `strategy_key` selezionabile da configurazione
- la `strategy_key` deve essere risolta contro un registry chiuso nel codice
- `capacity_from_containers_v1` resta logica fissa di setup, non switchabile
- i parametri numerici non devono essere hardcoded nel codice applicativo

## Acceptance Criteria

- esiste una configurazione interna V2 per scegliere la strategy di `monthly_stock_base_qty`
- esiste una configurazione interna V2 per i parametri numerici delle logiche stock V1
- il Core stock metrics puo leggere:
  - `strategy_key`
  - `params_json`
  - parametri della capacity logic fissa
- `capacity_from_containers_v1` resta non switchabile

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base alle migration e ai test backend introdotti.

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Nuovo package** `core/stock_policy/` — punto di raccolta per tutte le logiche stock V1.

**Alembic migration** `20260413_023_stock_logic_config.py`:
- Crea `core_stock_logic_config` con colonne: `monthly_base_strategy_key`, `monthly_base_params_json (JSON)`, `capacity_logic_key`, `capacity_logic_params_json (JSON)`, `updated_at`

**`config_model.py`**: ORM `CoreStockLogicConfig` — singleton (max 1 riga, id=1)

**`config.py`**:
- `KNOWN_MONTHLY_BASE_STRATEGIES = ["monthly_stock_base_from_sales_v1"]` — registry chiuso
- `CAPACITY_LOGIC_KEY = "capacity_from_containers_v1"` — costante fissa (non switchabile)
- `StockLogicConfig` — read model frozen con `monthly_base_strategy_key`, `monthly_base_params: dict`, `capacity_logic_key`, `capacity_logic_params: dict`, `is_default: bool`, `updated_at`
- `get_stock_logic_config(session)` — legge da DB, fallback ai default se tabella vuota
- `set_stock_logic_config(session, ...)` — upsert singleton; valida `strategy_key` contro registry; `capacity_logic_key` e immutabile

**Comportamento chiave:**
- se nessuna riga in DB: `is_default=True`, strategy=`monthly_stock_base_from_sales_v1`, params=`{}`
- strategy sconosciuta: `ValueError` (non HTTP error — validazione al livello di chiamata)
- `capacity_logic_key` sempre forzato a `CAPACITY_LOGIC_KEY` anche in update (non modificabile via API)
- `params_json` e opaco in questo slice — la struttura sarà definita in TASK-V2-084

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

