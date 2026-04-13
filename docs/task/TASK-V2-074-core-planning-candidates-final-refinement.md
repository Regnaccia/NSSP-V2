# TASK-V2-074 - Core Planning Candidates: final refinement

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

## Goal

Chiudere il refinement finale del Core `Planning Candidates` prima
dell'apertura del modulo `Production Proposals`.

## Context

`Planning Candidates` supporta gia:

- `planning_mode = by_article`
- `planning_mode = by_customer_order_line`

Prima di aprire `Production Proposals` il planning deve consolidare:

- clamp generale della giacenza negativa a `0` lato logica
- `reason_code` e `reason_text` espliciti
- descrizione ordine nel ramo `by_customer_order_line`
- esposizione della misura

## Scope

- introdurre la regola generale:
  - `stock_effective = max(stock_calculated, 0)`
  - valida per tutto `Planning Candidates`
- assicurare che stock negativo non generi candidate per il solo fatto di essere negativo
- aggiungere `reason_code` e `reason_text` nel read model / contratto Core
- nel ramo `by_customer_order_line` usare come descrizione primaria quella della riga ordine
- esporre anche la `misura` nel read model
- mantenere separata la futura gestione delle anomalie (`Warnings`)

## Out of Scope

- modulo `Warnings`
- `Production Proposals`
- scoring
- planning horizon
- nuove policy di aggregazione
- modifiche UI

## Constraints

- il clamp a `0` deve valere in entrambi i rami:
  - `by_article`
  - `by_customer_order_line`
- `stock_calculated` puo restare disponibile come dato tecnico, ma la logica planning deve usare solo `stock_effective`
- la `reason` deve essere sempre esplicita nel candidate
- la descrizione ordine deve prevalere sulla descrizione anagrafica nel ramo `by_customer_order_line`

## Acceptance Criteria

- il Core `Planning Candidates` usa `stock_effective = max(stock_calculated, 0)` per tutta la logica del modulo
- un articolo con `stock_calculated < 0` e nessun need reale non genera candidate
- tutti i candidate espongono:
  - `reason_code`
  - `reason_text`
- i candidate `by_customer_order_line` espongono:
  - descrizione ordine
  - misura
- il contratto Core/API e coerente con il refinement definito in `DL-ARCH-V2-028`

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati sul Core planning
- casi espliciti:
  - stock negativo senza need reale
  - ramo `by_article`
  - ramo `by_customer_order_line`
  - descrizione ordine e misura esposte correttamente

## Completed At

2026-04-10

## Completed By

Claude Code

## Completion Notes

- `effective_stock(inventory_qty)` aggiunta in `logic.py`: `max(inventory_qty, 0)` — None trattato come 0
- `_list_by_article_candidates` in `queries.py` ora calcola `avail_eff = stock_eff - set_aside - committed` usando il valore clamped; `availability_qty` nel read model riflette questo valore
- `_list_by_customer_order_line_candidates` usa `riga.article_description_segment` come descrizione primaria (`order_line_description`); fallback sull'anagrafica solo per `display_label`
- `PlanningCandidateItem` aggiornato con campi obbligatori `reason_code`, `reason_text` e opzionali `misura`, `order_line_description`
- `__init__.py` esporta `effective_stock` in `__all__`
- `types/api.ts` allineato al contratto V2 con i nuovi campi
- Frontend build pulita (zero errori TypeScript)

## Verification Notes

- 58 test `tests/core/test_core_planning_candidates.py` — tutti verdi
- Casi coperti: stock negativo senza need reale (no candidate), `by_article`, `by_customer_order_line`, descrizione ordine e misura esposte
- `npm run build` — zero errori

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

