# TASK-V2-093 - UI famiglie stock policy defaults

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

## Goal

Rendere accessibili nella UI `famiglie articolo` i default stock di famiglia:

- `stock_months`
- `stock_trigger_months`

in coerenza con il modello gia introdotto.

## Context

Il modello V2 supporta gia i default stock a livello famiglia e il Core li usa per calcolare:

- `effective_stock_months`
- `effective_stock_trigger_months`

ma oggi la surface `famiglie` espone solo:

- `considera_in_produzione`
- `aggrega_codice_in_produzione`

Quindi una parte della configurazione gia presente nel dominio non e ancora governabile da UI.

## Scope

- estendere la surface `famiglie articolo` per mostrare:
  - `stock_months`
  - `stock_trigger_months`
- permettere la modifica dei due default di famiglia
- chiarire in UI che questi valori hanno senso solo per articoli con:
  - `planning_mode = by_article`
- aggiornare eventuali endpoint / write flow necessari per salvare i due campi
- mantenere coerente la distinzione tra:
  - policy planning booleane
  - policy stock quantitative

## Refresh / Sync Behavior

- La vista `famiglie articolo` non introduce un refresh semantico backend nuovo
- Dopo il salvataggio, la UI deve mostrare il valore aggiornato della famiglia
- Eventuali effetti downstream su `articoli`, metriche stock e planning restano demand-driven dai refresh gia esistenti delle rispettive surface

## Out of Scope

- override articolo stock
- metriche stock calcolate
- configurazione strategy / params delle logiche stock
- integrazione in `Planning Candidates`

## Constraints

- nessuna logica di calcolo lato frontend
- i default stock restano nullable
- la UI non deve mostrare i campi in modo fuorviante come se valessero per `by_customer_order_line`

## Acceptance Criteria

- la tabella `famiglie articolo` mostra `stock_months` e `stock_trigger_months`
- i due valori sono modificabili dalla UI
- il salvataggio aggiorna il catalogo senza introdurre nuovi refresh semantici
- la distinzione tra planning booleane e stock quantitative resta chiara

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```powershell
python -m pytest tests/ -v
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Aggiunto `set_famiglia_stock_policy(session, code, stock_months, stock_trigger_months)` in `core/articoli/queries.py`
- Esportato da `core/articoli/__init__.py`
- Aggiunto `SetFamigliaStockPolicyRequest` e endpoint `PATCH /produzione/famiglie/{code}/stock-policy` in `app/api/produzione.py`
- Esteso `FamigliaRow` in `frontend/src/types/api.ts` con `stock_months: string | null` e `stock_trigger_months: string | null`
- Aggiornato `FamigliePage.tsx`: due input numerici inline per riga (stock mesi / trigger mesi) con mini form + pulsante "Salva" che appare solo quando dirty; nota in UI che i valori valgono solo per `by_article`
- 851 test verdi

## Completed At

2026-04-13

## Completed By

Claude Code
