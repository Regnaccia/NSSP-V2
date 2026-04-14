# TASK-V2-095 - Admin stock logic separate page

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

- `docs/task/TASK-V2-090-admin-stock-logic-config.md`
- `docs/task/TASK-V2-094-admin-stock-logic-dedicated-section-and-capacity-params.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`

## Goal

Separare la governance delle logiche stock dalla pagina utenti in `admin`, introducendo una pagina dedicata con routing proprio.

## Context

`TASK-V2-094` ha migliorato la separazione visiva dentro la stessa pagina `admin`, ma il requisito corretto e piu forte:

- pagina utenti
- pagina stock logic config

distinte e navigabili separatamente dentro il modulo `admin`.

La configurazione delle logiche stock e una capability di governance trasversale e non deve restare accorpata alla pagina utenti.

## Scope

- introdurre una pagina admin dedicata alle logiche stock
- mantenere la pagina utenti focalizzata solo su:
  - utenti
  - ruoli
  - stato attivo/inattivo
- spostare nella nuova pagina admin dedicata:
  - strategy `monthly_base_*`
  - parametri strategy
  - `capacity_logic_key`
  - `capacity_logic_params`
- aggiornare la navigazione admin per rendere raggiungibili entrambe le pagine
- preservare i contratti API gia introdotti

## Refresh / Sync Behavior

- Le pagine admin non introducono refresh semantici backend nuovi
- Ogni pagina ricarica solo la propria configurazione/risorsa dopo il salvataggio
- Nessun impatto sui refresh operativi di `articoli` o `planning`

## Out of Scope

- cambiare il contratto API stock logic
- cambiare la formula Core di capacity
- introdurre nuove strategy
- modificare il dominio warnings

## Constraints

- nessuna regressione sulla pagina utenti esistente
- nessun accorpamento UI residuo tra utenti e stock logic
- la nuova pagina deve restare interna al modulo `admin`

## Acceptance Criteria

- esistono due pagine admin distinte:
  - utenti
  - stock logic config
- la pagina utenti non contiene piu la configurazione stock
- la pagina stock logic contiene tutta la governance gia introdotta in `090/094`
- la navigazione admin rende esplicita la distinzione

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

- Creata `AdminStockLogicPage.tsx`: pagina autonoma con header + form completo (strategy params + capacity params), estratta da `AdminHome`
- `AdminHome.tsx` riscritto: contiene solo gestione utenti (tabella, modale crea, modale ruoli); layout ora usa `flex flex-col h-full` coerente con le altre surface
- Aggiunta route `GET /admin/stock-logic` in `App.tsx` con `ProtectedRoute roles=['admin']`
- Aggiunta voce "Logiche stock" in `SURFACE_FUNCTIONS.admin` in `AppShell.tsx` (dopo Utenti, prima di Warning Config)
- 851 test verdi

## Completed At

2026-04-13

## Completed By

Claude Code
