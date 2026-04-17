# TASK-V2-134 - Core proposal multi bar note fragment FASCI

## Status
Completed

## Date
2026-04-16

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-131-core-proposal-multi-bar-v1-logic.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`

## Goal

Correggere la note policy della logica multi-bar affinche l'output verso `note_fragment` non usi `BAR xN`, ma un frammento dedicato:

- `FASCI xN`

## Context

La logica:

- `proposal_multi_bar_v1_capacity_floor`

e semanticamente distinta dalle logiche `full_bar`.

Quindi anche il frammento note deve distinguere:

- barra intera classica:
  - `BAR xN`
- multi-bar / fasci:
  - `FASCI xN`

Questo migliora la leggibilita operativa della proposal e impedisce di confondere due modalita produttive diverse.

## Scope

- aggiornare la note policy della logica `proposal_multi_bar_v1_capacity_floor`
- rendere `FASCI xN` il frammento note canonico per questa logic
- aggiungere test backend mirati

## Out of Scope

- modifica delle formule quantitative della logic multi-bar
- redesign UI proposal
- cambi alle logiche `proposal_full_bar_v1` e `proposal_full_bar_v2_capacity_floor`

## Constraints

Regole:

- `proposal_full_bar_v1` e `proposal_full_bar_v2_capacity_floor` continuano a usare:
  - `BAR xN`
- `proposal_multi_bar_v1_capacity_floor` usa:
  - `FASCI xN`
- `N` resta il numero di unita lotto/barra/fascio effettivamente usato nel ramo finale (`ceil` o `floor`)

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 04 - Core read model prima della UI`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La correzione si applica nel normale path di generazione del workspace proposal.

## Acceptance Criteria

- `proposal_multi_bar_v1_capacity_floor` genera `note_fragment = FASCI xN`
- le logiche full-bar restano su `BAR xN`
- i test backend coprono il nuovo frammento note della logic multi-bar

## Deliverables

- correzione Core della note policy multi-bar
- eventuale riallineamento docs/spec se necessario
- test backend mirati

## Verification Level

- `None`

## Environment Bootstrap

```bash
cd backend
pip install -e .[dev]
```

## Verification Commands

```bash
python -m pytest V2/backend/tests/core/test_core_production_proposals.py V2/backend/tests/core/test_core_proposal_full_bar_v1.py -q
```

Atteso: exit code `0`.

## Implementation Log

### `core/production_proposals/logic.py`

`compute_note_fragment` modificato: aggiunta condizione dedicata per `proposal_multi_bar_v1_capacity_floor`
prima del branch `_FULL_BAR_LOGIC_KEYS`.

```python
if logic_key == "proposal_multi_bar_v1_capacity_floor":
    bars = params_snapshot.get("_bars_required")
    if bars is not None:
        return f"FASCI x{bars}"
elif logic_key in _FULL_BAR_LOGIC_KEYS:
    bars = params_snapshot.get("_bars_required")
    if bars is not None:
        return f"BAR x{bars}"
```

Le logiche `proposal_full_bar_v1` e `proposal_full_bar_v2_capacity_floor` continuano a restituire `BAR xN`.

### `tests/core/test_core_proposal_full_bar_v1.py`

`test_multi_bar_note_fragment`: aggiornata asserzione da `BAR x3` → `FASCI x3`.

**Esito:** `59 passed` in 1.98s.
