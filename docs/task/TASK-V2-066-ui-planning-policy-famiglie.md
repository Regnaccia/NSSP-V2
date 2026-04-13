# TASK-V2-066 - UI planning policy famiglie

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/task/TASK-V2-025-ui-tabella-famiglia-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`
- `docs/task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md`

## Goal

Estendere la UI della tabella `famiglie articolo` per gestire in modo esplicito i default di planning policy introdotti nel modello.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-063`

## Context

Con `TASK-V2-063` il modello `famiglie articolo` e stato esteso per supportare default di planning policy:

- `considera_in_produzione`
- `aggrega_codice_in_produzione`

Oggi la UI del catalogo famiglie espone e rende modificabile solo:

- `considera_in_produzione`

Serve ora riallineare la schermata alla nuova semantica del modello, in modo che il catalogo famiglie resti il luogo naturale dove governare le policy di default.

## Scope

### In Scope

- aggiornare la vista `famiglie articolo` per mostrare anche:
  - `aggrega_codice_in_produzione`
- permettere la modifica di `aggrega_codice_in_produzione` dalla UI dedicata
- chiarire testualmente che:
  - `considera_in_produzione` e un default di planning policy
  - `aggrega_codice_in_produzione` e un default di aggregazione per codice
- aggiornare il contratto UI/backend solo se necessario a supportare la nuova colonna/azione
- aggiornare documentazione minima della schermata

### Out of Scope

- UI di override articolo
- consumo delle policy nei moduli `criticita` o `planning candidates`
- redesign completo della schermata famiglie
- nuove policy oltre alle due gia fissate

## Constraints

- la schermata famiglie deve restare dedicata ai default di catalogo, non alle eccezioni articolo
- la UI deve restare leggibile e tabellare
- il task non deve introdurre logiche operative nuove, ma solo rendere governabili quelle gia introdotte nel modello

## Refresh / Sync Behavior

`La vista non ha refresh on demand`

Questo task non introduce o modifica refresh semantici backend.

## Acceptance Criteria

- la schermata `famiglie articolo` mostra `aggrega_codice_in_produzione`
- l'utente puo modificare `aggrega_codice_in_produzione` dalla UI
- il significato di entrambe le colonne e leggibile e coerente col modello
- la schermata continua a distinguere chiaramente i default di famiglia dalle future eccezioni articolo
- `npm run build` passa

## Deliverables

- refinement UI della tabella famiglie
- eventuale adeguamento contract/backend minimo se necessario
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Task di refinement UI su schermata gia esistente.

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm install
```

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- trattare la schermata famiglie come gestione dei default
- evitare di presentare qui concetti di override o effective policy
- usare naming UI esplicito e non ambiguo

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Modifiche backend

- `core/articoli/read_models.py` — aggiunto campo `aggrega_codice_in_produzione: bool` a `FamigliaRow`
- `core/articoli/queries.py` — aggiornate tutte le costruzioni di `FamigliaRow` (catalog, create, toggle_active, toggle_considera); aggiunta funzione `toggle_famiglia_aggrega_codice_produzione`
- `app/api/produzione.py` — aggiunto endpoint `PATCH /famiglie/{code}/aggrega-codice-produzione`; importata la nuova funzione

### Modifiche frontend

- `types/api.ts` — aggiunto campo `aggrega_codice_in_produzione: boolean` a `FamigliaRow`
- `pages/surfaces/FamigliePage.tsx`:
  - aggiunto `handleToggleAggrega` con stato `togglingAggrega`
  - aggiunta colonna "Aggrega codice" nella tabella (header + cella checkbox per riga)
  - intestazione "In produzione" arricchita con tooltip esplicativo

### Verifica

- `pytest tests/core/test_core_planning_policy.py` → 23 passed
- `npm run build` → OK (313 kB, 0 errori TypeScript)

## Completed At

2026-04-10

## Completed By

Claude Code
