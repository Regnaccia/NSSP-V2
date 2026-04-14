# TASK-V2-098 - UI articoli override gestione scorte attiva

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

Rendere configurabile nella UI `articoli` l'override:

- `override_gestione_scorte_attiva`

e mostrare il valore:

- `effective_gestione_scorte_attiva`

## Scope

- estendere il dettaglio `articoli`
- mostrare valore effettivo e override tri-state
- aggiornare il write flow articolo per salvare l'override
- mantenere distinta la semantica:
  - `planning_mode`
  - `gestione_scorte_attiva`

## Out of Scope

- consumo Core del flag in stock metrics / planning

## Constraints

- nessuna logica di calcolo lato frontend
- UI coerente col pattern gia usato per gli altri override articolo

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

Esteso il dettaglio articolo con override tri-state e valore effettivo per `gestione_scorte_attiva`:

- **`read_models.py` (ArticoloDetail)**: aggiunto `override_gestione_scorte_attiva: bool | None`
- **`queries.py`**: aggiunto `set_articolo_gestione_scorte_override(session, codice, value)`; `get_articolo_detail` restituisce `override_gestione_scorte_attiva`
- **`__init__.py`**: esporta `set_articolo_gestione_scorte_override`
- **`produzione.py`**: aggiunto `SetGestioneScorteOverrideRequest` + endpoint `PATCH /articoli/{codice}/gestione-scorte-override`
- **`api.ts`**: aggiunto `effective_gestione_scorte_attiva: boolean | null` e `override_gestione_scorte_attiva: boolean | null` a `ArticoloDetail`
- **`ProduzioneHome.tsx`**: aggiunto `gestiSaveStatus`, `handleGestioneScorteChange`, `handleGestioneScorteOverrideChange`; nella sezione "Planning policy" aggiunto select tri-state con effective label e nota esplicativa; prop `onGestioneScorteOverrideChange` passato a `ColonnaDettaglio`

Pattern coerente con gli altri override articolo (tri-state select + effective label). Semantica `gestione_scorte_attiva` mantenuta distinta da `planning_mode`. 864 test passano.

## Completed At

2026-04-13

## Completed By

Claude Code
