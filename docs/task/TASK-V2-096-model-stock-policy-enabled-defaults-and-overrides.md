# TASK-V2-096 - Model stock policy enabled defaults and overrides

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

## Goal

Introdurre nel modello V2 un flag esplicito di applicabilita della stock policy:

- default famiglia
- override articolo
- valore effettivo nel Core `articoli`

## Context

Oggi la stock policy e implicita su tutti gli articoli `by_article`.
Serve invece poter distinguere:

- articoli `by_article` con gestione scorte attiva
- articoli `by_article` con gestione scorte disattivata

## Scope

- aggiungere a livello famiglia:
  - `gestione_scorte_attiva`
- aggiungere a livello articolo:
  - `override_gestione_scorte_attiva`
- esporre nel Core `articoli`:
  - `effective_gestione_scorte_attiva`
- applicare la stessa regola di precedenza gia usata per le altre planning policy

## Out of Scope

- UI famiglia / UI articolo
- consumo del flag nel Core stock policy o planning

## Constraints

- nessuna lettura diretta da Easy
- default famiglia + override articolo + effective value devono restare il pattern standard

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

Introdotto il flag esplicito di applicabilita della stock policy:

- **`models.py` (ArticoloFamiglia)**: aggiunto `gestione_scorte_attiva: bool` (default False, NOT NULL)
- **`models.py` (CoreArticoloConfig)**: aggiunto `override_gestione_scorte_attiva: bool | None` (tri-state nullable)
- **`read_models.py` (FamigliaRow)**: aggiunto `gestione_scorte_attiva: bool = False`
- **`read_models.py` (ArticoloDetail)**: aggiunto `effective_gestione_scorte_attiva: bool | None = None`
- **`queries.py`**: aggiornato `_famiglia_to_row`; aggiunto `toggle_famiglia_gestione_scorte`; `get_articolo_detail` risolve `effective_gestione_scorte_attiva` con la stessa regola di precedenza delle altre policy
- **`__init__.py`**: esporta `toggle_famiglia_gestione_scorte`
- **Migrazione** `20260413_024_gestione_scorte_attiva.py`: `ADD COLUMN gestione_scorte_attiva BOOLEAN NOT NULL DEFAULT FALSE` su `articolo_famiglie` + `ADD COLUMN override_gestione_scorte_attiva BOOLEAN` su `core_articolo_config`

864 test passano.

## Completed At

2026-04-13

## Completed By

Claude Code
