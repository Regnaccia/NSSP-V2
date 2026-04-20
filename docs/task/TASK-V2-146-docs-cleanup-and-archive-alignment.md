# TASK-V2-146 - Docs cleanup and archive alignment

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/roadmap/CLEANUP_PLAN_2026-04-17.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-041.md`
- `docs/decisions/ARCH/DL-ARCH-V2-043.md`

## Goal

Pulire la documentazione attiva della V2, archiviando o marcando i materiali non piu guida del rebase.

## Scope

- identificare i documenti non piu guida
- marcare i documenti superseded dove serve
- riallineare indici `README`, overview e handoff
- mantenere tracciabilita storica senza lasciare concorrenza tra documenti attivi e documenti ormai superati

## Out of Scope

- cancellazione fisica in massa dei DL
- rimozione di task storici completati
- modifiche Core o UI

## Constraints

- i documenti storici vanno preferibilmente archiviati o marcati, non cancellati
- il baseline attivo del rebase deve restare immediatamente riconoscibile dagli indici

## Acceptance Criteria

- gli indici documentali puntano in modo chiaro ai documenti guida correnti
- i documenti superseded non competono piu con quelli attivi
- nessun documento storico utile viene perso

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-19

**`docs/roadmap/STATUS.md`**

- Aggiornato "Decision log attivi": `ARCH/ fino a DL-ARCH-V2-043` (era V2-041).

**`docs/AI_HANDOFF_CURRENT_STATE.md`**

- Aggiunto `DL-ARCH-V2-042` e `DL-ARCH-V2-043` alla sezione "Active Architectural Guidance".
- Aggiornata la sezione `Planning Candidates` (surface 6) con:
  - `priority_score` come layer separato baseline V1
  - `stock_effective_qty`, `open_order_lines`, `nearest_delivery_date` nel ramo by_article
  - Rebase note completa: customer_horizon_days rimosso dal Core, classificazione ora lineare
- Aggiornata sezione "Current Open Tasks": aggiunti TASK-135, 136, 146, 147, 148.
- Aggiornata sezione "What Is The Next Logical Reasoning Area": ora punta a navigation cleanup e workspace UX evolution.
- Aggiornata "How To Use The Existing Docs" con DL-039 -> DL-043.
- Aggiornato "Practical Summary".

**`docs/SYSTEM_OVERVIEW.md`**

- Aggiunto `DL-ARCH-V2-042` e `DL-ARCH-V2-043` alla nota di baseline.
- Aggiornata sezione `Planning Candidates`:
  - Aggiunto `priority_score`, `stock_effective_qty`, `open_order_lines`, `nearest_delivery_date`.
  - Sostituita la sezione "Non ancora disponibile: scoring" con il rebase completato.
  - Rebase target residuo: solo workspace UX evolution.
- Aggiornati i task aperti correnti (aggiunti 135, 136, 146, 147, 148).
- Aggiunto ai Pattern: `priority_score` come layer separato e `customer_horizon` declassato.

**`docs/README.md`**

- Aggiunte le righe mancanti nella tabella task: TASK-V2-076 -> TASK-V2-148 (erano presenti solo fino a V2-075).

**`docs/guides/PLANNING_AND_STOCK_RULES.md`**

- Sezione 10 "Customer Horizon" riscritta per riflettere il rebase:
  - `customer_horizon_days` non piu nel calcolo Core
  - Uso residuo: filtro UI, proximity nel priority_score, flag is_within_customer_horizon
  - Classificazione planning ora lineare e non dipendente dall'orizzonte
- Aggiunta nuova sezione 10.1 "Priority Score" con formula baseline V1 e regole di separazione.
- Aggiunta ai References: DL-ARCH-V2-042 e DL-ARCH-V2-043.

**Documenti non modificati / non necessari**

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`: gia aggiornato (sezione 9.3C allineata al rebase).
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`: nessun riferimento a customer_horizon in Core.
- DL storici (001-038): invariati, storici validi.
- Task storico README: gia completo con tutti i task 001-148.
