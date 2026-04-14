# TASK-V2-110 - Unify planning candidate description model

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date
2026-04-14

## Owner
Claude Code

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-032.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Unificare il modello descrittivo di `Planning Candidates` introducendo un contratto canonico
comune per i rami `by_article` e `by_customer_order_line`.

## Context

Oggi i due rami usano forme descrittive diverse:

- `by_article` usa la descrizione sintetica del Core `articoli`
- `by_customer_order_line` usa descrizione ordine, con struttura piu ricca derivata da
  `description_lines`

Serve convergere verso:

- `description_parts`
- `display_description`

prendendo `by_customer_order_line` come riferimento semantico del modello.

## Scope

- introdurre nel read model `PlanningCandidateItem`:
  - `description_parts`
  - `display_description`
- costruire `description_parts` nel ramo `by_customer_order_line` come:
  - `[article_description_segment, ...description_lines]`
- costruire `description_parts` nel ramo `by_article` come:
  - `[descrizione_1, descrizione_2]`
- filtrare segmenti vuoti preservando l'ordine
- derivare `display_description` da `description_parts`
- usare `article_code` come fallback finale se la lista e vuota
- mantenere compatibilita temporanea con i campi descrittivi storici gia esposti, se necessario

## Out of Scope

- badge UI
- palette famiglie
- destinazione richiesta
- data richiesta
- future proposal

## Constraints

- la UI non deve piu dover conoscere due modelli descrittivi diversi
- il ramo `by_customer_order_line` resta il riferimento semantico del modello
- il ramo `by_article` non deve simulare una descrizione di ordine quando non esiste

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `Si`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `No`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `No`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Pattern References

- `Pattern 2 - Mirror esterno + arricchimento interno`
- `Pattern 16 - Core unico, segmentazione solo in UI`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- ogni candidate espone `description_parts`
- ogni candidate espone `display_description`
- il ramo `by_customer_order_line` usa i segmenti descrittivi completi aggregati dal Core ordini
- il ramo `by_article` usa la forma `[descrizione_1, descrizione_2]`
- fallback finale a `article_code` solo se la lista segmenti e vuota

## Deliverables

- read model `Planning Candidates` esteso
- query Core planning riallineate
- test mirati sul contratto descrittivo unificato

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude sul Core `Planning Candidates`.

## Implementation Notes

- se `108` e in corso, questo task ha precedenza sul modello descrittivo e puo richiedere un
  riallineamento del task stesso

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Esteso `PlanningCandidateItem` con `description_parts` e `display_description`.
- Uniformata la costruzione descrittiva nel Core:
  - `by_article` -> `[descrizione_1, descrizione_2]`
  - `by_customer_order_line` -> `[article_description_segment, ...description_lines]`
- Implementato fallback canonico a `article_code` quando i segmenti sono vuoti.
- Allineata la UI al contratto unico (`description_parts` multilinea, fallback `display_description`).
- Aggiornati i test Core Planning Candidates sul nuovo contratto descrittivo.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
