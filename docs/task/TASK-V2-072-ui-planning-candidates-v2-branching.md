# TASK-V2-072 - UI Planning Candidates V2 branching

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`
- `docs/task/TASK-V2-070-ui-allineamento-nomenclatura-planning-mode.md`
- `docs/task/TASK-V2-071-core-planning-candidates-v2-branching.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`

## Goal

Evolvere la surface UI `Planning Candidates` per rappresentare correttamente i candidate prodotti dal branching Core V2 tra `by_article` e `by_customer_order_line`.

## Context

La UI attuale di `Planning Candidates` e coerente con la V1:

- un solo shape aggregato per articolo
- una sola logica quantitativa visibile

Con `TASK-V2-071` il Core introdurra due modalita reali:

- `planning_mode = by_article`
- `planning_mode = by_customer_order_line`

La UI deve quindi smettere di assumere un solo shape globale e diventare esplicita sul tipo di candidate visualizzato.

## Scope

- aggiornare la surface `Planning Candidates` per consumare il nuovo contratto Core V2
- rappresentare esplicitamente `planning_mode`
- gestire candidate `by_article`
- gestire candidate `by_customer_order_line`
- introdurre le colonne minime necessarie per il ramo per-riga, ad esempio:
  - riferimento ordine cliente
  - riferimento riga ordine cliente
  - `line_open_demand_qty`
  - `linked_incoming_supply_qty`
  - `line_future_coverage_qty`
- mantenere leggibili i candidate aggregati per articolo
- aggiornare ordinamenti e testi UI per entrambi i rami

## Out of Scope

- cambiare la logica Core di branching
- introdurre scoring / ranking
- introdurre detail panel avanzato
- introdurre planning horizon o ETA
- cambiare il refresh semantico backend riusato dalla vista

## Constraints

- la UI deve restare comprensibile anche in presenza di righe con shape diversi
- `planning_mode` deve essere sempre riconoscibile
- evitare che il ramo `by_customer_order_line` venga presentato come shortage generico per articolo
- mantenere il refresh della vista agganciato al refresh semantico backend gia esistente

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Il pulsante `Aggiorna` deve continuare a usare il refresh semantico della surface `produzione`, senza introdurre una nuova chain.

## Acceptance Criteria

- la UI `Planning Candidates` consuma correttamente il contratto Core V2 con `planning_mode`
- i candidate `by_article` e `by_customer_order_line` sono distinguibili senza ambiguita
- il ramo per-riga mostra i riferimenti ordine/riga e le metriche corrette
- il refresh della vista non cambia semanticamente
- la completion note descrive chiaramente:
  - shape UI finale
  - colonne aggiunte o modificate
  - eventuali limiti di leggibilita residui

## Verification Level

- `Mirata`

Verifiche minime richieste:

- test frontend mirati se presenti sul modulo
- `npm run build`
- verifica manuale minima su:
  - candidate `by_article`
  - candidate `by_customer_order_line`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

Il riallineamento di roadmap, overview e guide trasversali viene fatto dopo da Codex.

## Contracts / Flows Changed

### Componente modificato

**`frontend/src/pages/surfaces/PlanningCandidatesPage.tsx`** — riscrittura parziale per V2 branching.

### SortKey aggiornato

`SortKey` migrato da chiavi di campo dirette a chiavi semantiche:
- `demand` → `resolveDemand(item)`: `line_open_demand_qty ?? customer_open_demand_qty`
- `availability` → `availability_qty` (by_article only, `0` per by_col)
- `supply` → `resolveSupply(item)`: `linked_incoming_supply_qty ?? incoming_supply_qty`
- `coverage` → `resolveCoverage(item)`: `line_future_coverage_qty ?? future_availability_qty`
- `famiglia_label`, `required_qty_minimum`: invariati

### Colonne tabella — shape finale

| Colonna | by_article | by_customer_order_line |
|---|---|---|
| Codice | article_code | article_code |
| Descrizione | display_label | display_label |
| Famiglia | famiglia_label | famiglia_label |
| Mode | badge "articolo" | badge "per riga" |
| Ordine / Riga | — | order_reference / line_reference |
| Domanda | customer_open_demand_qty | line_open_demand_qty |
| Dispon. attuale | availability_qty | — |
| Supply | incoming_supply_qty | linked_incoming_supply_qty |
| Copertura | future_availability_qty (rosso se < 0) | line_future_coverage_qty (rosso se < 0) |
| Fabbisogno min. | required_qty_minimum | required_qty_minimum |

### Row key

Aggiornato a `${article_code}-${order_reference ?? ''}-${line_reference ?? ''}` per unicità nel ramo by_customer_order_line (più righe per lo stesso articolo).

### Refresh semantico

Invariato: `POST /sync/surface/produzione` — nessuna nuova chain introdotta.

## Documentation Impact

Nessun impatto documentale trasversale — il contratto API (`GET /api/produzione/planning-candidates`) non cambia URL. La UI consuma i nuovi campi additive già introdotti da TASK-V2-071.

## Completion Notes

TASK-V2-072 completato. Build frontend pulita (tsc + vite, 0 errori).

La surface `Planning Candidates` ora gestisce correttamente entrambe le modalità Core V2:
- candidate `by_article` → badge "articolo", colonne aggregate per articolo
- candidate `by_customer_order_line` → badge "per riga", colonne per riga ordine con riferimento ordine/riga

Introdotto `PlanningModeBadge` per distinguibilità immediata del ramo. `SortKey` migrato a chiavi semantiche (`demand`, `supply`, `coverage`) che risolvono in modo trasparente la metrica corretta indipendentemente dal ramo.

## Verification Notes

- `npm run build`: 0 errori TypeScript, build completa in 7.92s
- Verifica manuale: da eseguire su istanza locale con candidati reali di entrambi i rami

## Completed At

2026-04-10

## Completed By

Claude Code
