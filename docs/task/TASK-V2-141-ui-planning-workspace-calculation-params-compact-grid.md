# TASK-V2-141 - UI planning workspace: parametri di calcolo in griglia compatta

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-140-ui-planning-workspace-calculation-params-and-right-config.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`

## Goal

Rifinire il blocco centrale `Parametri di calcolo` per schermi wide, evitando che:

- label e valori risultino troppo distanti
- il badge di provenienza sia scollegato dal valore
- le unita siano rese come elementi separati e poco leggibili

## Context

Nel layout attuale del blocco `Parametri di calcolo`, su schermi larghi:

- la label resta troppo a sinistra
- valore e provenienza finiscono all'estrema destra
- la relazione visiva tra descrizione e valore si indebolisce

Serve quindi un refinement puramente UI che mantenga il contenuto gia concordato ma migliori la leggibilita.

## Scope

- trasformare il blocco `Parametri di calcolo` in una griglia compatta a larghezza controllata
- usare una riga a tre colonne logiche:
  - `label`
  - `value`
  - `source badge`
- tenere il bottone `Override` separato nell'header del blocco
- rendere i valori con unita in forma compatta quando applicabile

## Out of Scope

- modifica dei campi mostrati nel blocco
- modifica della scheda destra `Planning / Scorte`
- nuovi parametri di calcolo
- cambi backend o API

## Constraints

### Layout

Il blocco non deve usare una riga full-width con:

- label tutta a sinistra
- valore tutto a destra

Target richiesto:

- contenitore interno con larghezza controllata
  oppure
- sub-grid con associazione visiva stretta tra `label`, `value` e `source`

La forma preferita e:

- `label | value | source badge`

### Header

Il pulsante:

- `Override`

deve restare nell'header del blocco e non entrare nella griglia dei valori.

### Rendering valori

Quando applicabile, il valore deve includere l'unita in forma compatta:

- `30 gg`
- `3 mesi`
- `1.5 mesi`

e non come unita separata troppo distante dal numero.

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `DL-UIX-V2-002` pattern multi-colonna

## Refresh / Sync Behavior

- `La view riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- il blocco `Parametri di calcolo` non usa piu un layout stretched su tutta la larghezza disponibile
- ogni riga rende leggibile l'associazione tra:
  - label
  - valore
  - provenienza
- il badge di provenienza resta vicino al valore
- `Override` resta nell'header del blocco
- i valori con unita sono mostrati in forma compatta
- il build frontend resta verde

## Deliverables

- refinement UI del blocco centrale `Parametri di calcolo`

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

### `frontend/src/pages/surfaces/PlanningWorkspacePage.tsx`

**Rimosso `FieldRowProvenance`** (non più necessario dopo la migrazione alla griglia).

**`BloccoParametriDiCalcolo` — layout sostituito con griglia CSS 3-col:**
- Container: `display: grid; gridTemplateColumns: max-content max-content max-content` con `gap-x-3 gap-y-1.5`
- Colonne: `label | value | source badge` — ogni colonna `max-content` → nessun stretching, associazione visiva stretta
- Separatore: `<div style={{ gridColumn: '1 / -1' }}` che occupa tutta la larghezza della griglia
- Campi derivati (senza provenienza): cella badge = `<span />` vuoto per mantenere l'allineamento della griglia

**Unità compatte aggiunte:**
- `effective_stock_months` → `{val} mesi`
- `effective_stock_trigger_months` → `{val} mesi`
- `horizonDays` → `{val} gg` (era già presente, ora coerente con il pattern)

**Esito build:** `✓ built in 3.62s`, exit code `0`.

### Estensione — griglia applicata agli altri blocchi centrali

Su richiesta, lo stesso pattern è stato applicato a tutti i blocchi che usavano `FieldRow`:

**`FieldRow` refactored → React Fragment (2 celle, nessun wrapper div):**
- Rimosso `justify-between`, rimosso `py-0.5`, rimosso `text-right`
- I due `<span>` (label + value) partecipano direttamente alla CSS grid del parent

**Blocchi aggiornati con grid container `max-content auto`:**
- `BloccoNeedVsRelease` (entrambi i rami: by_article e by_customer_order_line)
- `BloccoClienteOrdine` (con righe condizionali — il Fragment vuoto è trasparente al grid)
- `BloccoStockCapienza`

Pattern uniforme per tutti i blocchi:
```tsx
<div className="border rounded-lg p-3">
  <BlockHeader title="..." />
  <div className="items-baseline gap-y-1.5"
       style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}>
    <FieldRow ... />
    {condition && <FieldRow ... />}
  </div>
</div>
```

**Esito build post-estensione:** `✓ built in 3.63s`, exit code `0`.
