# TASK-V2-155 - Core proposal status: rivedere il blocco rigido su `line_reference`

## Status
Completed

## Date
2026-04-20

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-151-core-proposal-panel-contracts.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`

## Goal

Rivedere la semantica che oggi marca `proposal_status = Error` quando manca `line_reference`, evitando falsi bloccanti sui candidate aggregati `by_article`.

## Context

Oggi il preview proposal nel planning marca come errore bloccante:

- casi `customer`
- o `by_customer_order_line`

quando `line_reference` e assente.

Questo comportamento appare troppo rigido rispetto all'export EasyJob realmente accettato, soprattutto per i candidate aggregati `by_article`.

## Scope

- rileggere la regola `ordine_linea_mancante`
- distinguere almeno:
  - `by_customer_order_line`
  - `by_article`
- evitare che l'assenza di `line_reference` renda automaticamente non esportabile un candidate aggregato

## Out of Scope

- redesign UI della colonna destra
- writer export finale xlsx completo
- override proposal

## Acceptance Criteria

- i candidate `by_article` non vanno automaticamente in `Error` solo per `line_reference` assente
- i casi veramente bloccanti restano distinguibili
- `proposal_status` resta coerente con il comportamento export reale
- test mirati coprono almeno:
  - caso `by_article` aggregato senza `line_reference`
  - caso `by_customer_order_line` con `line_reference` assente

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-20

1085 test passati (6 nuovi, tutti verdi).

**Root cause**: la condizione originale marcava come `Error` qualsiasi candidate con
`primary_driver == "customer"` e `line_reference is None`, includendo i candidate
`by_article` aggregati che per definizione non hanno mai un `line_reference`.

**Fix** (`core/planning_candidates/queries.py` — `_compute_proposal_preview_v1`):
```python
# Prima (errato):
ordine_linea_mancante = (
    (item.primary_driver == "customer" or item.planning_mode == "by_customer_order_line")
    and item.line_reference is None
)

# Dopo (corretto, TASK-V2-155):
ordine_linea_mancante = (
    item.planning_mode == "by_customer_order_line"
    and item.line_reference is None
)
```

La semantica corretta: solo i candidate `by_customer_order_line` hanno un
`line_reference` esplicito richiesto dall'export EasyJob; la sua assenza è bloccante
solo per questa modalità. Per `by_article` l'aggregazione è per codice articolo e
il `line_reference` è sempre `None` per design.

**Nuovo file di test** (`tests/core/test_core_proposal_status_line_reference.py`):
- `test_by_article_customer_driver_no_line_reference_not_error` — caso chiave del bug
- `test_by_article_stock_driver_no_line_reference_not_error`
- `test_by_customer_order_line_missing_line_reference_is_error` — errore bloccante confermato
- `test_by_customer_order_line_with_line_reference_not_error`
- `test_error_reason_summary_for_missing_line_reference`
- `test_by_article_customer_reason_summary_contains_qty`
