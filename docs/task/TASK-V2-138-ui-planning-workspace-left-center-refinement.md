# TASK-V2-138 - UI planning workspace left + center refinement

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-137-ui-planning-unified-workspace-shadow-view-left-center.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/decisions/ARCH/DL-ARCH-V2-041.md`

## Goal

Rifinire la shadow view del `Unified Planning Workspace` gia introdotta in `TASK-V2-137`, riallineando in modo puntuale:

- gerarchia visiva della colonna sinistra
- ordine e contenuto dei blocchi della colonna centrale

al contratto UIX congelato dopo la review UX.

## Context

`TASK-V2-137` ha aperto la nuova shadow view planning con colonne sinistra + centrale.

Dopo la prima iterazione sono state fissate in spec alcune scelte piu precise:

- card sinistra con gerarchia per righe
- `required_qty_eventual` come quantita sintetica allineata a destra
- triangolo warning come unico segnale minimo
- blocco centrale `Identita` senza `cliente_scope_label`
- blocco `Cliente / Ordine` subito dopo `Identita`
- ordine finale dei blocchi centrali:
  - `Identita`
  - `Cliente / Ordine`
  - `Need vs Release`
  - `Stock / Capienza`
  - `Motivo`
  - `Warnings`

Questo task serve a portare l'implementazione UI allo stato della spec, senza ancora toccare la colonna destra proposal.

## Scope

- rifinire la colonna sinistra della shadow view secondo la gerarchia congelata
- rifinire la colonna centrale della shadow view secondo i blocchi e l'ordine congelati
- mantenere la vista planning legacy disponibile per confronto
- non introdurre ancora la colonna destra

## Out of Scope

- colonna destra proposal
- batch export
- override proposta
- nuovi contratti backend
- sostituzione della vista planning legacy
- redesign della pagina `Production Proposals`

## Constraints

### Colonna sinistra

La card deve seguire questo ordine:

1. `cliente_scope_label`
   - con triangolo warning in alto a destra se esiste almeno un warning
2. `article_code - measure`
   - stesso peso visivo
3. `display_description`
4. `requested_destination_display + requested_delivery_date`
   - solo se esiste componente customer
5. badge stati:
   - `proposal_status`
   - `workflow_status`
   - `release_status`

Quantita sintetica:

- `required_qty_eventual`
- allineata a destra nella card

### Colonna centrale

Ordine blocchi:

1. `Identita`
2. `Cliente / Ordine`
3. `Need vs Release`
4. `Stock / Capienza`
5. `Motivo`
6. `Warnings`

Regole specifiche:

- `Identita` non mostra `cliente_scope_label`
- `Identita` mostra:
  - `article_code - measure`
  - `display_description`
  - triangolo warning se presente
- `Cliente / Ordine` include:
  - `cliente_scope_label`
  - `requested_destination_display`
  - `requested_delivery_date`
  - `order_reference`
  - `line_reference`
- nel caso `by_customer_order_line` il blocco `Cliente / Ordine` non deve duplicare la descrizione ordine, gia espressa in `display_description`
- nei casi `stock-only` il blocco `Cliente / Ordine` sparisce del tutto

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
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `DL-UIX-V2-002` pattern multi-colonna

## Refresh / Sync Behavior

- `La view riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- la colonna sinistra segue la gerarchia visiva congelata in spec
- `required_qty_eventual` e visibile come quantita sintetica allineata a destra
- il triangolo warning compare solo come segnale minimo
- la colonna centrale rispetta il nuovo ordine dei blocchi
- `Identita` non mostra `cliente_scope_label`
- `Cliente / Ordine` sparisce nei casi `stock-only`
- nel caso `by_customer_order_line` non viene duplicata la descrizione ordine nel blocco `Cliente / Ordine`
- il build frontend resta verde

## Deliverables

- refinement della shadow view planning introdotta in `TASK-V2-137`
- eventuali helper UI collegati

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

**Colonna sinistra — `CandidateCard` (gerarchia congelata):**
- Riga 1: `ScopeBadge` (cliente_scope_label) + triangolo ▲ warning top-right
- Riga 2: `article_code – misura` + `resolveQtySintetica` allineata a destra
- Riga 3: `display_description`
- Riga 4: `requested_destination_display · data` — solo se `hasCustomer`
- Riga 5: badge `proposal_status` / `workflow_status` / `release_status`
- Aggiunto `resolveQtySintetica`: usa `required_qty_eventual` con fallback su `required_qty_minimum`

**Colonna centrale — nuovo ordine blocchi:**
`Identità → Cliente/Ordine → Need vs Release → Stock/Capienza → Motivo → Warnings`

**`BloccoIdentita` (1):**
- Rimosso `cliente_scope_label`
- Aggiunto triangolo ▲ warning top-right se `active_warnings.length > 0`
- Mostra: `article_code – misura`, `famiglia_label`, `display_description`

**`BloccoClienteOrdine` (2):**
- Aggiunto `ScopeBadge` con `cliente_scope_label` come prima riga
- Nascosto per `stock-only` (`primary_driver === 'stock'` e `by_article`)
- Per `by_customer_order_line`: omessa `full_order_line_description` (già in `display_description` → `BloccoIdentita`)
- Campo `order_reference / line_reference` mostrato quando disponibile in entrambi i rami

**Esito build:** `✓ built in 3.72s`, exit code `0`.

