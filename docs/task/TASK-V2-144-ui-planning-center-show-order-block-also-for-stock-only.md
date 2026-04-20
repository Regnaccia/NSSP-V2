# TASK-V2-144 - UI planning center: mostrare Cliente / Ordine anche nei casi stock-only

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/task/TASK-V2-143-ui-planning-center-open-orders-and-stock-effective.md`

## Goal

Riallineare la colonna centrale del `Unified Planning Workspace` alla nuova decisione UX:

- il blocco `Cliente / Ordine` deve restare visibile anche nei casi `stock-only`
- la sottosezione `Ordini aperti` deve quindi rendere leggibili anche gli impegni cliente futuri che non generano shortage cliente entro orizzonte

## Context

La decisione precedente nascondeva il blocco `Cliente / Ordine` nei casi `stock-only`.

Questo comportamento non e piu desiderato, perche proprio nei casi `stock-only` e utile vedere:

- gli ordini aperti esistenti
- la loro distribuzione temporale
- quali ricadono entro l'`Orizzonte cliente`
- quali restano oltre

Così si evita di leggere il caso come "solo scorta astratta" quando in realtà esistono impegni cliente futuri già noti.

## Scope

- mantenere visibile il blocco `Cliente / Ordine` anche nei candidate `stock-only`
- mantenere visibile la sottosezione `Ordini aperti` quando esistono righe aperte
- non richiedere shortage cliente attivo per mostrare il blocco

## Out of Scope

- modifica delle formule planning
- pannello destro
- redesign della colonna sinistra

## Constraints

- nel ramo `by_article`, il blocco `Cliente / Ordine` resta visibile anche se:
  - `customer_shortage_qty = 0`
  - `primary_driver = stock`
- la sottosezione `Ordini aperti` continua a usare:
  - `open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)`
- il blocco puo avere header sintetico ridotto nei casi `stock-only`, ma non deve sparire

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No, salvo piccoli allineamenti se la UI filtra localmente
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Refresh / Sync Behavior

- `La view riusa il refresh semantico backend esistente`

## Acceptance Criteria

- il blocco `Cliente / Ordine` non sparisce piu nei casi `stock-only`
- la sottosezione `Ordini aperti` e visibile quando esistono righe aperte, anche con `primary_driver = stock`
- la UI continua a distinguere visivamente:
  - `entro orizzonte`
  - `oltre orizzonte`
- il build frontend resta verde

## Deliverables

- refinement UI della colonna centrale

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
cd frontend
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### 2026-04-17

**Frontend — `PlanningWorkspacePage.tsx`**

- `BloccoClienteOrdine`: rimosso il guard `if (isStockOnly) return null` (e la variabile `isStockOnly` non più necessaria).
- Il blocco ora è sempre visibile per il ramo `by_article`, indipendentemente da `primary_driver`.
- Nei casi `stock-only` senza ordini aperti il blocco mostra solo il campo Scope ("Magazzino").
- Nei casi `stock-only` con righe aperte oltre orizzonte (che non hanno generato shortage cliente entro il filtro) la sottosezione `Ordini aperti` resta visibile con la distinzione blu/ambra per orizzonte.

**Verifica**

- `npm run build` → build verde
