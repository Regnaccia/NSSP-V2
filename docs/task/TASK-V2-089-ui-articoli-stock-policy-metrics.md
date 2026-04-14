# TASK-V2-089 - UI articoli stock policy metrics

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
- `docs/task/TASK-V2-083-model-stock-policy-defaults-and-overrides.md`
- `docs/task/TASK-V2-084-core-stock-policy-metrics-v1.md`

## Goal

Esporre nella surface `articoli` le principali entita stock calcolate e le configurazioni
stock effettive, distinguendo chiaramente tra:

- valori read-only calcolati
- override articolo modificabili

in modo coerente con il modello V2.

## Context

Dopo l'introduzione di:

- default/override della stock policy
- Core stock metrics V1

serve rendere questi dati leggibili nella surface `articoli`, prima di o in parallelo
all'uso operativo completo in `Planning Candidates`.

La surface `articoli` e gia il punto naturale in cui convivono:

- configurazione articolo-specifica
- valori effettivi risolti da famiglia + override
- metriche calcolate read-only

Quindi ha senso che alcuni campi stock siano anche modificabili da qui.

## Scope

- estendere il dettaglio `articoli` per mostrare in read-only:
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `monthly_stock_base_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`
- estendere il dettaglio `articoli` per mostrare e/o configurare:
  - `effective_stock_months`
  - `effective_stock_trigger_months`
  - `capacity_override_qty`
  - `override_stock_months`
  - `override_stock_trigger_months`
- chiarire in UI la distinzione tra:
  - configurazione
  - valore calcolato
  - valore effettivo
- mantenere la visualizzazione coerente con il `planning_mode` effettivo:
  - i campi stock hanno senso solo nel ramo `by_article`
- se utile, esporre anche metadati tecnici minimali:
  - `strategy_key`
  - `computed_at`

## Refresh / Sync Behavior

- La vista riusa il refresh semantico backend gia esistente della surface `articoli`
- Il task non deve introdurre un nuovo refresh separato
- La UI deve consumare i dati stock resi disponibili dal Core senza cambiare il contratto di refresh

## Out of Scope

- tuning admin dei parametri logici stock
- integrazione stock-driven in `Planning Candidates`
- warning o badge aggiuntivi

## Constraints

- la surface `articoli` resta consultiva per le metriche calcolate
- gli unici campi modificabili in questo task sono gli override articolo della stock policy
- nessuna logica di calcolo lato frontend
- nessuna esposizione fuorviante dei campi stock per articoli `by_customer_order_line`

## Acceptance Criteria

- il dettaglio `articoli` mostra metriche e configurazioni stock rilevanti
- la UI distingue chiaramente:
  - mesi stock / mesi trigger
  - override articolo / valori effettivi
  - capacity calcolata / override / effettiva
  - base mensile / target / trigger
- gli override articolo stock sono modificabili dalla surface `articoli`
- i dati stock non vengono mostrati in modo ambiguo per articoli non `by_article`

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

**Nuovi campi in `ArticoloDetail` (`core/articoli/read_models.py`):**
- `override_stock_months`, `override_stock_trigger_months`: override articolo-specifici (writable)
- `monthly_stock_base_qty`, `capacity_calculated_qty`, `capacity_effective_qty`: metriche calcolate (read-only)
- `target_stock_qty`, `trigger_stock_qty`: target/trigger calcolati (read-only)
- `stock_computed_at`, `stock_strategy_key`: metadati del calcolo (read-only)

**`get_articolo_detail` (`core/articoli/queries.py`):**
- Chiama `list_stock_metrics_v1(session)` e filtra per `article_code` → popola i nuovi campi
- Già espone `override_stock_months` e `override_stock_trigger_months` dalla config (erano letti ma non restituiti)
- Le metriche sono `None` per articoli senza `planning_mode = by_article`

**`set_articolo_stock_policy_override` (nuova funzione in queries.py):**
- Imposta `override_stock_months`, `override_stock_trigger_months`, `capacity_override_qty`
- Pattern sentinel identico a `set_articolo_policy_override`
- Esportata da `core/articoli/__init__.py`

**Nuovo endpoint `PATCH /api/produzione/articoli/{codice}/stock-policy-override`:**
- Body: `override_stock_months`, `override_stock_trigger_months`, `capacity_override_qty` (tutti nullable)
- Restituisce `ArticoloDetail` aggiornato con metriche ricalcolate
- Converte `float | None` → `Decimal | None` prima di passare al Core

**Frontend `ProduzioneHome.tsx`:**
- Sezione "Stock policy V1 — by_article" visibile solo se `detail.planning_mode === 'by_article'`
- Metriche calcolate in riquadro read-only: base mensile, capacity calcolata/effettiva, target, trigger, mesi effettivi, timestamp/strategia
- Form override con 3 input: mesi scorta, mesi trigger, capacity override — placeholder mostra il valore effettivo ereditato
- `handleStockPolicyOverrideChange`: chiama `PATCH stock-policy-override` e aggiorna `detail`
- Stato locale (`stockMonthsInput`, `stockTriggerInput`, `capacityOverrideInput`) reset al cambio articolo

**`types/api.ts`:** `ArticoloDetail` esteso con i 9 nuovi campi stock

**Nessuna regressione:** 830 test passano.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`
