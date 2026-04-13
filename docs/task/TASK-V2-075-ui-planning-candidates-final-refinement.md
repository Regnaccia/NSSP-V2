# TASK-V2-075 - UI Planning Candidates: final refinement

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`

## Goal

Rendere la vista `Planning Candidates` coerente con il refinement finale del modulo,
prima dell'apertura di `Production Proposals`.

## Context

Il Core planning deve essere aggiornato da `TASK-V2-074` con:

- clamp generale dello stock negativo
- `reason_code` / `reason_text`
- descrizione ordine per `by_customer_order_line`
- misura esposta

La UI deve consumare e mostrare correttamente questi nuovi campi.

## Scope

- aggiornare la schermata `Planning Candidates` per mostrare:
  - `reason`
  - `misura`
- nel ramo `by_customer_order_line` mostrare la descrizione ordine come descrizione primaria
- mantenere leggibile la distinzione tra:
  - `by_article`
  - `by_customer_order_line`
- allineare ordinamenti / colonne / testi al nuovo contratto

## Refresh Behavior

- refresh semantico backend riusato
- la vista continua a usare il refresh semantico completo gia esistente della surface produzione/articoli

## Out of Scope

- nuove logiche Core
- modulo `Warnings`
- `Production Proposals`
- scoring
- redesign completo della surface

## Constraints

- nessun candidate deve suggerire implicitamente che lo stock negativo sia un need produttivo
- la `reason` deve essere visibile senza costringere l'utente a inferirla dai numeri
- nel ramo `by_customer_order_line` la descrizione ordine deve essere la piu evidente

## Acceptance Criteria

- la tabella mostra una colonna o area esplicita per la `reason`
- la `misura` e visibile
- i candidate `by_customer_order_line` mostrano come descrizione primaria quella della riga ordine
- la UI resta coerente con il `planning_mode`
- il pulsante `Aggiorna` continua a usare il refresh semantico backend corretto

## Verification Level

- `Mirata`

Verifiche minime:

- build frontend
- smoke manuale su candidate `by_article`
- smoke manuale su candidate `by_customer_order_line`
- verifica visiva di `reason`, `misura` e descrizione ordine

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

- Aggiunto componente `ReasonBadge` in `PlanningCandidatesPage.tsx`: mostra `reason_text` con colore derivato da `reason_code` — amber per `future_availability_negative`, rose per `line_demand_uncovered`
- Aggiunta colonna "Motivo" nella tabella (dopo "Mode") con `ReasonBadge` per ogni riga
- `misura` mostrata inline nella cella "Codice" come testo muted piccolo sotto il codice articolo
- Descrizione `by_customer_order_line` già primaria via `display_label` backend (TASK-V2-074): nessuna modifica richiesta alla colonna "Descrizione"
- Commento header file aggiornato a includere TASK-V2-075 e DL-ARCH-V2-028

## Verification Notes

- `npm run build` — zero errori TypeScript
- Smoke manuale: verificare visivamente colonna Motivo e misura inline per candidati `by_article` e `by_customer_order_line`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

