# TASK-V2-069 - Allineamento nomenclatura planning_mode

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

- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`

## Goal

Introdurre nel modello e nei contratti il vocabolario esplicito `planning_mode`, riallineando la semantica oggi implicita nel flag `effective_aggrega_codice_in_produzione`.

## Context

Con `DL-ARCH-V2-027` il modulo `Planning Candidates` non e piu descritto correttamente come un semplice booleano di aggregazione acceso/spento.

Esistono ora due modalita planning esplicite:

- `by_article`
- `by_customer_order_line`

Il sistema usa gia il driver di policy:

- `effective_aggrega_codice_in_produzione`

ma prima di evolvere il Core `Planning Candidates` alla V2 conviene introdurre una nomenclatura esplicita e stabile, per evitare che:

- codice
- contratti Core/API
- UI
- task futuri

continuino a ragionare in termini di booleano opaco invece che di modalita di planning.

## Scope

- introdurre nel Core il concetto esplicito di `planning_mode`
- mappare in modo centrale:
  - `effective_aggrega_codice_in_produzione = true` -> `planning_mode = by_article`
  - `effective_aggrega_codice_in_produzione = false` -> `planning_mode = by_customer_order_line`
- esporre `planning_mode` nei contratti/read model dove oggi e utile preparare il branching V2
- riallineare naming interni, helper e commenti di codice dove il concetto e gia emerso
- aggiornare le completion notes del task con i punti toccati e i contratti cambiati

## Out of Scope

- cambiare gia la logica Core di `Planning Candidates` alla V2
- introdurre il branch `by_customer_order_line` nei candidate reali
- modificare la UI `Planning Candidates`
- rimuovere il flag persistito `effective_aggrega_codice_in_produzione`

## Constraints

- il task deve essere puramente di nomenclatura/contratto
- `effective_aggrega_codice_in_produzione` resta il driver dati di policy
- `planning_mode` e il vocabolario esplicito derivato, non una seconda configurazione indipendente
- evitare refactor larghi non necessari: lo scopo e preparare il V2 Core, non anticiparlo

## Refresh / Sync Behavior

La vista non ha refresh on demand.

## Acceptance Criteria

- esiste una mappatura centrale e univoca da `effective_aggrega_codice_in_produzione` a `planning_mode`
- i contratti Core toccati usano il vocabolario `planning_mode` dove serve preparare il branching V2
- nessun comportamento planning cambia ancora nel risultato funzionale della V1 attuale
- la completion note dichiara esplicitamente quali read model / helper / contratti sono stati riallineati

## Verification Level

- `Mirata`

Verifiche minime richieste:

- test backend mirati sui contratti/helper toccati
- eventuali test Core aggiornati per la mappatura `true -> by_article`, `false -> by_customer_order_line`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

Il riallineamento di roadmap, overview e guide trasversali viene fatto dopo da Codex.

## Contracts / Flows Changed

**Nuovo modulo** `nssp_v2/core/planning_mode.py` — unica sorgente autorevole del vocabolario:
- `PlanningMode = Literal["by_article", "by_customer_order_line"]`
- `resolve_planning_mode(effective_aggrega: bool | None) -> PlanningMode | None`

**Read model aggiornati:**
- `PlanningCandidateItem` (`core/planning_candidates/read_models.py`): aggiunto campo `planning_mode: PlanningMode | None`
- `ArticoloDetail` (`core/articoli/read_models.py`): aggiunto campo `planning_mode: PlanningMode | None`
- `ArticoloItem` (`core/articoli/read_models.py`): campi `effective_*` resi opzionali con default `None` (non breaking)

**Query aggiornate:**
- `list_planning_candidates_v1`: popola `planning_mode` via `resolve_planning_mode`
- `get_articolo_detail`: popola `planning_mode` via `resolve_planning_mode`

**Contratti API:** nessun endpoint modificato — i campi sono aggiunti ai read model già esposti.

**Frontend types** (`V2/frontend/src/types/api.ts`):
- aggiunto `export type PlanningMode = 'by_article' | 'by_customer_order_line'`
- aggiunto `planning_mode: PlanningMode | null` a `PlanningCandidateItem` e `ArticoloDetail`

**Risoluzione circular import:** `planning_mode.py` spostato da `core/planning_candidates/` a `core/` (livello neutro senza dipendenze dai package `articoli` o `planning_candidates`). Il vecchio file `planning_candidates/planning_mode.py` è stato eliminato.

**Comportamento planning V1 invariato:** il branching `by_article` / `by_customer_order_line` è preparato ma non ancora biforcato — la logica V1 di candidatura rimane identica.

## Documentation Impact

Nessun impatto documentale trasversale — riallineamento puramente di nomenclatura/contratto.

## Completion Notes

TASK-V2-069 completato senza regressioni. 629 test backend passati. Build frontend pulita.

Il vocabolario `planning_mode` è ora il termine di dominio esplicito in tutti i contratti Core/API/frontend che preparano il branching V2. `effective_aggrega_codice_in_produzione` resta il driver dati persistito; `planning_mode` è il vocabolario derivato.

## Verification Notes

- `tests/core/test_core_planning_mode.py` — 5 test sulla mappatura centrale `resolve_planning_mode` (True/False/None)
- `tests/core/test_core_planning_candidates.py` — 44 test (inclusi TestForzaCompletata da TASK-V2-068) tutti passati
- Suite completa: 629 passed, 0 failed
- Frontend: build TypeScript + Vite pulita

## Completed At

2026-04-10

## Completed By

Claude Code
