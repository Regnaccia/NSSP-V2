# TASK-V2-097 - UI famiglie gestione scorte attiva

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

Rendere configurabile nella UI `famiglie articolo` il default:

- `gestione_scorte_attiva`

## Scope

- estendere la surface `famiglie articolo`
- mostrare il flag `gestione_scorte_attiva`
- permettere la modifica del default famiglia
- chiarire che vale solo come prerequisito della stock policy nel ramo `by_article`

## Out of Scope

- override articolo
- metriche stock calcolate
- configurazione strategy/params admin

## Constraints

- nessuna logica di calcolo lato frontend

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

Estesa la surface famiglie articolo con il flag `gestione_scorte_attiva`:

- **`produzione.py`**: aggiunto endpoint `PATCH /famiglie/{code}/gestione-scorte` che inverte il flag tramite `toggle_famiglia_gestione_scorte`
- **`api.ts`**: aggiunto `gestione_scorte_attiva: boolean` a `FamigliaRow`
- **`FamigliePage.tsx`**: aggiunta colonna "Gestione scorte" con checkbox toggle; nota aggiornata per chiarire che Stock mesi / Trigger mesi valgono solo per by_article con gestione scorte attiva

Dipende da TASK-V2-096 (implementato contestualmente). 864 test passano.

## Completed At

2026-04-13

## Completed By

Claude Code
