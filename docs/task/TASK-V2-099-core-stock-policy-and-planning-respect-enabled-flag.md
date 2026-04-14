# TASK-V2-099 - Core stock policy and planning respect enabled flag

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date
2026-04-13

## Owner
Claude Code

## Source Documents

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
- `docs/task/TASK-V2-096-model-stock-policy-enabled-defaults-and-overrides.md`

## Goal

Applicare `effective_gestione_scorte_attiva` al consumo Core della stock policy e del planning stock-driven.

## Scope

- escludere dalla stock policy gli articoli `by_article` con gestione scorte disattivata
- evitare il calcolo / consumo stock-driven dove il flag effettivo e `false`
- riallineare `Planning Candidates by_article` al nuovo prerequisito

## Out of Scope

- UI famiglia
- UI articolo
- warnings aggiuntivi

## Constraints

- `planning_mode = by_article` resta prerequisito necessario
- `effective_gestione_scorte_attiva = true` diventa prerequisito aggiuntivo

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```powershell
python -m pytest tests/ -v
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Applicato `effective_gestione_scorte_attiva` come prerequisito aggiuntivo (oltre a `planning_mode = by_article`) sia nel Core stock policy che nel planning candidates.

**`stock_policy/queries.py`**:
- Aggiunto blocco filtro dopo quello di `effective_aggrega`: risolve `override_gestione_scorte_attiva` (da `CoreArticoloConfig`) e `gestione_scorte_attiva` (da `ArticoloFamiglia`); esclude l'articolo se `effective_gestione != True`
- Aggiornato docstring modulo: perimetro ora include entrambi i prerequisiti

**`planning_candidates/queries.py`**:
- Aggiunto `effective_gestione_scorte: bool | None` a `_ArticoloInfo`
- `_load_articoli_info` risolve il flag con la stessa regola di precedenza override > famiglia
- `_list_by_article_candidates`: lookup stock metrics condizionato a `art.effective_gestione_scorte is True` — se disattivato, `trigger_qty = None` e `target_qty = None` (nessuna candidatura da stock trigger, ma la shortage resta)
- Aggiornati commenti docstring

**Test** (871 passano, 7 nuovi):
- `test_core_stock_policy_metrics.py`: aggiunto `gestione_scorte_attiva=True` default agli helper `_famiglia` e `_config`; 5 nuovi test per `gestione_scorte_attiva = False`, override True/False, lista mista
- `test_core_planning_candidates_stock.py`: aggiunto `gestione_scorte_attiva=True` default; 2 nuovi test (trigger escluso senza flag, shortage ancora attiva)
- `test_core_warnings.py`: aggiunto `gestione_scorte_attiva=True` default a `_famiglia_w`

## Completed At

2026-04-13

## Completed By

Claude Code
