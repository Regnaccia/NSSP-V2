# TASK-V2-088 - Stock policy final alignment before planning

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
- `docs/task/TASK-V2-087-hardening-monthly-stock-base-algorithm.md`

## Goal

Chiudere i delta residui tra l'implementazione reale della stock policy V1 e il profilo
semantico concordato, prima di integrare la logica in `Planning Candidates`.

## Context

Dopo `TASK-V2-087` l'algoritmo `monthly_stock_base_from_sales_v1` e molto piu vicino al
profilo V1 concordato, ma restano ancora alcuni disallineamenti puntuali:

- fallback implementato a `None` invece che a `0`
- `min_movements` non ancora implementato
- `rounding_scale` non ancora implementato
- perimetro `planning_mode = by_article` non ancora esplicitato nel computed slice
- driver vendita non ancora fissato in modo esplicito nel calcolo dei movimenti

`TASK-V2-085` non dovrebbe partire lasciando questi punti impliciti.

## Scope

- decidere e implementare il fallback finale di `monthly_stock_base_qty`:
  - `0` oppure `None`, coerente con spec e test
- introdurre il parametro `min_movements`
- introdurre il parametro `rounding_scale`
- esplicitare nel computed slice il perimetro corretto degli articoli:
  - solo `planning_mode = by_article`
- fissare in modo esplicito il driver movimenti V1 della strategy
  - usando il perimetro corretto disponibile nei mirror V2
- aggiornare test, task notes e doc se necessario

## Out of Scope

- nuove strategy stock
- modifica delle formule `target_stock_qty` / `trigger_stock_qty`
- integrazione in `Planning Candidates`
- UI/admin per tuning parametri

## Constraints

- nessuna lettura diretta da Easy
- nessuna regressione sul modello di configurazione introdotto in `TASK-V2-086`
- il risultato deve essere coerente con `STOCK_POLICY_V1_REDUCED_SPEC`

## Acceptance Criteria

- non restano delta aperti tra implementazione reale e profilo V1 documentato
- `monthly_stock_base_qty` ha fallback esplicito e testato
- `min_movements` e `rounding_scale` sono implementati e testati
- il computed slice applica esplicitamente il perimetro `by_article`
- il driver movimenti V1 e definito in modo non ambiguo

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

**Fallback `None` (decisione esplicita):**
- `estimate_monthly_stock_base_from_sales_v1` restituisce `None` (non `0`) quando i dati sono insufficienti
- `None` = "incalcolabile" (dati mancanti), `Decimal("0")` = "consumo reale zero"
- Documentato esplicitamente nel docstring della funzione

**Nuovi params `min_movements` e `rounding_scale`:**
- `min_movements` (default `0` = disabilitato): soglia globale sul numero di righe movimento nel periodo; se non raggiunta → `None` immediato
- `rounding_scale` (default `None` = nessun arrotondamento): se configurato, applica `quantize(ROUND_HALF_UP)` al risultato finale
- Il `total_movements: int = 0` viene passato come argomento alla funzione pura; il conteggio viene aggregato nella query via `COUNT(*)` per articolo+mese

**Filtro `planning_mode = by_article` (TASK-V2-088):**
- `list_stock_metrics_v1` ora include **solo** articoli con `effective_aggrega_codice_in_produzione = True`
- La risoluzione usa lo stesso schema tri-state: `override_aggrega` (da `CoreArticoloConfig`) vince su `family_aggrega` (da `ArticoloFamiglia`)
- Articoli con `effective_aggrega = None` o `False` vengono saltati con `continue`

**Driver movimenti V1 (esplicito):**
- Aggiunto filtro `SyncMagReale.quantita_scaricata > 0` alla query
- Definisce "uscita di magazzino" come driver V1: esclude resi, rettifiche negative, movimenti a zero
- Nessun filtro su `causale_movimento_codice` in V1 (tutte le causali con scarico positivo contano)

**Modifiche ai file:**
- `core/stock_policy/logic.py`: nuovi params + signature `total_movements=0`
- `core/stock_policy/queries.py`: `COUNT(*)` in aggregazione, filtro `> 0`, `by_article` skip, passaggio `total_movements`
- `tests/core/test_core_stock_policy_logic.py`: 8 nuovi test (fallback None, min_movements, rounding_scale)
- `tests/core/test_core_stock_policy_metrics.py`: 9 nuovi test (planning mode filter, driver movimenti, min_movements integrazione)

**Verifiche:**
```
python -m pytest tests/core/test_core_stock_policy_logic.py tests/core/test_core_stock_policy_metrics.py -v
# 91 passed
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

