# TASK-V2-107 - Planning Candidates requested delivery date

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
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Aumentare la leggibilita di `Planning Candidates` esponendo in tabella la data richiesta con
semantica coerente per i due rami.

## Context

Nel ramo `by_customer_order_line` la data richiesta e un dato naturale della riga ordine cliente.
Nel ramo `by_article` invece non esiste una singola data "vera", perche il candidate puo essere
aggregato e puo includere anche componente stock.

Serve quindi una regola esplicita:

- `by_customer_order_line` -> `requested_delivery_date`
- `by_article` -> `earliest_customer_delivery_date` solo se esiste componente customer
- `stock-only` -> nessuna data inventata

## Scope

- estendere il Core / read model `Planning Candidates` con:
  - `requested_delivery_date` nel ramo `by_customer_order_line`
  - `earliest_customer_delivery_date` nel ramo `by_article`
- definire la regola di calcolo del ramo `by_article`:
  - minima data cliente rilevante tra le righe che contribuiscono alla componente customer
- lasciare `null` / vuoto il campo nel caso `stock-only`
- esporre la colonna data nella tabella UI `Planning Candidates`
- adattare l'etichetta o il rendering in modo che non sembri una data promessa per i casi
  puramente stock-driven

## Out of Scope

- calcolo della futura `earliest_uncovered_due_date`
- prioritizzazione ordini
- lead time produttivi
- ETA produzioni
- nuove logiche di scheduling

## Constraints

- nessuna data deve essere inventata per candidate `stock-only`
- il ramo `by_article` non deve simulare una data di scorta
- la semantica deve restare spiegabile leggendo il dettaglio candidate

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `Si`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `No`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `Si`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- i candidate `by_customer_order_line` espongono `requested_delivery_date`
- i candidate `by_article` con componente customer espongono `earliest_customer_delivery_date`
- i candidate `by_article` `stock-only` non mostrano una data inventata
- la tabella UI `Planning Candidates` mostra la data in modo coerente con il planning mode

## Deliverables

- read model / query `Planning Candidates` esteso
- API `Planning Candidates` estesa
- tabella UI `Planning Candidates` aggiornata
- test mirati Core/UI sul rendering della data

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude su Core/UI `Planning Candidates`.

## Implementation Notes

- nel ramo `by_article` il campo puo essere derivato solo dal lato customer, non dalla componente
  stock
- se il candidate e misto, la data mostrata resta la prima data cliente rilevante

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Esteso read model `Planning Candidates` con:
  - `requested_delivery_date` per `by_customer_order_line`
  - `earliest_customer_delivery_date` per `by_article`
- Regola `by_article` implementata:
  - valorizzata solo quando la componente customer e attiva (`customer_shortage_qty > 0`)
  - `stock-only` mantiene `earliest_customer_delivery_date = null`
- Query Core aggiornata:
  - nel ramo `by_customer_order_line` la data arriva da `expected_delivery_date` della riga
  - nel ramo `by_article` la data minima e derivata dalle righe cliente aperte per articolo
- UI `Planning Candidates` aggiornata:
  - nuova colonna `Data richiesta`
  - rendering coerente per ramo:
    - `by_customer_order_line` -> `requested_delivery_date`
    - `by_article` customer/mixed -> `earliest_customer_delivery_date`
    - `stock-only` -> testo esplicito `solo scorta`
- Test Core aggiornati per:
  - popolamento `requested_delivery_date`
  - popolamento `earliest_customer_delivery_date` nel ramo customer
  - assenza data nei casi `stock-only`

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
