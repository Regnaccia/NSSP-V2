# TASK-V2-067 - UI override e effective policy articoli

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-023-ui-famiglia-articoli.md`
- `docs/task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md`
- `docs/task/TASK-V2-064-core-effective-planning-policy-articoli.md`

## Goal

Introdurre nella surface `articoli` la gestione delle planning policy a livello articolo, distinguendo chiaramente override puntuale e valori effettivi risultanti.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-063`
- `TASK-V2-064`

## Context

Con `TASK-V2-063` il modello articolo supporta override nullable per:

- `override_considera_in_produzione`
- `override_aggrega_codice_in_produzione`

Con `TASK-V2-064` il Core `articoli` espone gia:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`

Manca ancora la UI che permetta di:

- vedere le policy effettive
- configurare gli override del singolo articolo
- distinguere chiaramente tra:
  - default di famiglia
  - override articolo
  - risultato effettivo

## Scope

### In Scope

- aggiungere nel dettaglio `articoli` una sezione dedicata alle planning policy
- esporre in UI almeno:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
- introdurre controlli UI per configurare gli override articolo:
  - `eredita`
  - `true`
  - `false`
- rendere leggibile la distinzione tra:
  - default famiglia
  - override articolo
  - valore effettivo
- usare solo contratti backend/Core coerenti col modello gia introdotto
- aggiornare documentazione minima della surface `articoli`

### Out of Scope

- modifica della logica di `planning candidates`
- modifica della logica di `criticita`
- bulk edit degli override
- nuovi flag oltre alle due policy gia definite
- redesign generale della schermata `articoli`

## Constraints

- la UI deve rendere evidente il concetto di override nullable / tri-state
- il dettaglio articolo non deve confondere il default di famiglia con il valore effettivo
- i dati Easy e i fact quantitativi read-only devono restare visivamente separati dalle nuove configurazioni
- il task non deve ancora imporre il consumo dei nuovi campi nelle altre surface

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Questo task non modifica il comportamento di refresh della surface `articoli`:

- il pulsante `Aggiorna` continua a usare `refresh_articoli()`
- gli override articolo sono configurazioni interne, non richiedono una nuova chain semantica

## Acceptance Criteria

- la schermata `articoli` mostra i valori effettivi delle planning policy
- l'utente puo impostare gli override articolo in modalita tri-state
- la UI rende chiara la differenza tra default famiglia, override articolo e valore effettivo
- la schermata `articoli` continua a funzionare senza regressioni sul resto del pannello dettaglio
- `npm run build` passa

## Deliverables

- refinement UI del dettaglio `articoli`
- eventuale adeguamento contract/backend minimo se necessario
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Task di refinement UI su surface esistente.

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

- usare controlli semplici e espliciti per il tri-state
- mantenere la nuova sezione separata sia dai dati Easy sia dai fact quantitativi
- privilegiare leggibilita del modello rispetto a una UI troppo compatta

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Modifiche backend

**`core/articoli/read_models.py`**
- `ArticoloDetail` ora include `override_considera_in_produzione: bool | None` e `override_aggrega_codice_in_produzione: bool | None`

**`core/articoli/queries.py`**
- `get_articolo_detail` ora espone i valori override nel read model
- Aggiunta `set_articolo_policy_override(session, codice, override_considera, override_aggrega)` con pattern sentinel per modifiche selettive

**`core/articoli/__init__.py`**
- Esportate `set_articolo_policy_override` e `toggle_famiglia_aggrega_codice_produzione` (mancavano dall'`__init__`)

**`app/api/produzione.py`**
- Aggiunto `SetPolicyOverrideRequest` (override_considera + override_aggrega, entrambi nullable)
- Aggiunto endpoint `PATCH /produzione/articoli/{codice}/policy-override` — restituisce `ArticoloDetail` aggiornato

### Modifiche frontend

**`types/api.ts`**
- `ArticoloDetail` ora include `effective_considera_in_produzione`, `effective_aggrega_codice_in_produzione`, `override_considera_in_produzione`, `override_aggrega_codice_in_produzione`

**`pages/surfaces/ProduzioneHome.tsx`**
- `ColonnaDettaglio` riceve nuovo prop `onPolicyOverrideChange`
- Aggiunta sezione "Planning policy" con:
  - due `<select>` tri-state (Eredita / Sì / No) per ciascun override
  - label "Effettivo" colorata (verde Sì, grigio No, ambra Non definito)
  - stato `policySaveStatus` indipendente da `saveStatus` famiglia
- `handlePolicyOverrideChange` chiama `PATCH /produzione/articoli/{codice}/policy-override` e aggiorna `detail` con la risposta

### Pattern tri-state

- `"null"` → `null` → eredita dalla famiglia
- `"true"` → `true` → sovrascrive con true
- `"false"` → `false` → sovrascrive con false

### Verifica

- `pytest tests/core tests/app -q` → 376 passed
- `npm run build` → OK (316 kB, 0 errori TypeScript)

## Completed At

2026-04-10

## Completed By

Claude Code
