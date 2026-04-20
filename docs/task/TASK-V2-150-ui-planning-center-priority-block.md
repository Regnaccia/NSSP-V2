# TASK-V2-150 - UI planning center: blocco `Priority`

## Status
Completed

## Date
2026-04-19

## Owner
Codex

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-044.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/task/TASK-V2-149-core-ui-priority-score-v1-basic.md`

## Goal

Introdurre nella colonna centrale del workspace planning una sezione read-only:

- `Priority`

per spiegare `priority_score` e il dettaglio delle componenti di ranking.

## Scope

- aggiungere il blocco `Priority` sotto `Warnings`
- mostrare almeno:
  - `priority_score`
  - `priority_reason_summary`
- estendere, quando disponibile il contratto API, a:
  - `priority_band`
  - `priority_score_policy_key`
  - componenti score

## Out of Scope

- editing della policy score
- configurazione admin delle policy score
- variazione manuale del punteggio da UI
- formula del Core score

## Constraints

- il blocco resta read-only
- deve spiegare il punteggio, non sostituire `Motivo` o `Warnings`
- le penalita devono essere distinguibili dai contributi positivi
- il task deve restare separato da `TASK-V2-149`

## Acceptance Criteria

- il dettaglio centrale include il blocco `Priority`
- il blocco appare sotto `Warnings`
- `priority_score` e leggibile senza dover inferire il significato dai soli badge di sinistra
- se le componenti sono disponibili, vengono mostrate in modo auditabile
- se le componenti non sono ancora disponibili, il blocco usa il rollout minimo:
  - score totale
  - summary

## Deliverables

- delta UI sul workspace planning
- eventuale piccolo adattamento types/api
- riallineamento docs/task se il contratto API viene esteso

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-19

Delta UI-only. TypeScript compila pulito (0 errori).

**`PlanningWorkspacePage.tsx`**:
- Aggiunto componente `BloccoPriority` (blocco 7, dopo `BloccoWarnings`).
- Mostra: score numerico + banda colorata + tabella componenti derivate lato client.
- Componenti derivate: `time_urgency`, `customer_pressure`, `stock_pressure`, `release_penalty`,
  `warning_penalty` — ricalcolate dai campi gia presenti sul `PlanningCandidateItem` con la stessa
  logica del backend (DL-ARCH-V2-044), senza richiedere un campo `priority_components` separato.
- Riga di totale con riepilogo score finale.
- Se nessuna componente e attiva, mostra "Nessuna componente attiva — punteggio baseline."
- Il blocco e invisibile (ritorna `null`) se `priority_score` e null.
- Aggiornato commento modulo: ordine blocchi centrali include `→ Priority`.
- Aggiornato `README.md` task con stato completato.
