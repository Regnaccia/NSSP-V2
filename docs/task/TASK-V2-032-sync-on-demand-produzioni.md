# TASK-V2-032 - Sync on demand produzioni

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il trigger `sync on demand` backend-controlled per la surface `produzioni`.

Il task deve permettere alla UI di richiedere un refresh manuale del dominio `produzioni`,
mantenendo il controllo completo nel backend.

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/task/TASK-V2-028-sync-produzioni-attive.md`
- `docs/task/TASK-V2-029-sync-produzioni-storiche.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`

## Goal

Consentire alla surface `produzioni` di richiedere un refresh manuale dei dati, senza accesso diretto della UI a script o a Easy.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-028`
- `TASK-V2-029`
- `TASK-V2-030`
- `TASK-V2-031`

## Context

La V2 ha gia validato il pattern `sync on demand` per:

- `logistica`
- `articoli`

Per `produzioni` il refresh manuale deve seguire lo stesso modello:

- la UI richiede
- il backend valida
- il backend esegue
- la UI legge stato e freshness

## In Scope

- endpoint backend per richiedere il refresh `produzioni`
- orchestrazione backend delle sync necessarie per `produzioni`
- guard minime su permessi, concorrenza e disponibilita runtime
- action UI dedicata nella surface `produzioni`
- feedback minimo di stato nella UI

## Out of Scope

- scheduler automatico
- orchestrazione distribuita
- modifica del flag `forza_completata`
- nuovi filtri o configurazioni operative di produzione

## Constraints

- la UI non deve chiamare script direttamente
- la UI non deve parlare con Easy
- il backend resta unico orchestratore del refresh
- il task deve restare coerente con `DL-ARCH-V2-011`

## Acceptance Criteria

- esiste un trigger backend per il refresh manuale di `produzioni`
- la surface `produzioni` espone un'azione UI dedicata per richiedere il refresh
- la UI riceve feedback minimo di esecuzione
- nessun accesso diretto ai mirror `sync_*` dal frontend
- `npm run build` passa senza errori
- le verifiche backend del trigger passano

## Deliverables

- endpoint/backend command per `sync on demand produzioni`
- integrazione UI nella surface `produzioni`
- eventuali test backend o smoke test coerenti
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- endpoint/command introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Modificati:**
- `src/nssp_v2/app/api/sync.py` — aggiunta costante `_PRODUZIONI_ENTITIES`, helper `_build_freshness` (refactoring freshness logistica/produzione), endpoint `POST /sync/surface/produzioni`, endpoint `GET /sync/freshness/produzioni`; import `EasyProduzioneAttivaSource` e `EasyProduzioneStoricaSource`
- `frontend/src/pages/surfaces/ProduzioniPage.tsx` — aggiunta `FreshnessBar`, logica `syncStatus`, `freshness`, `handleRefresh`, `loadFreshness`

### Endpoint/command introdotti

- `POST /api/sync/surface/produzioni` — trigger sync `produzioni_attive` + `produzioni_storiche`; 503 se Easy non configurato; 409 se sync concorrente
- `GET  /api/sync/freshness/produzioni` — freshness di `produzioni_attive` e `produzioni_storiche`

### Refactoring collaterale

Il corpo duplicato della freshness (logistica, produzione) è stato estratto nell'helper privato `_build_freshness(session, entity_codes, threshold_seconds)`. Nessun comportamento cambiato.

### Test eseguiti

- `python -m pytest tests -q` → 307/307 passed
- `npm run build` → ✓ (build pulita)

### Test non eseguiti

- Test HTTP degli endpoint sync/freshness produzioni: non inclusi; il pattern è identico a logistica/produzione già coperti, e `SyncRunner` + le sync unit sono già testate in isolamento.

### Assunzioni

- Le entità `produzioni_attive` e `produzioni_storiche` non hanno dipendenze tra loro (dichiarate `DEPENDENCIES: []` in entrambe le unit): possono essere eseguite in qualsiasi ordine.
- Il threshold di staleness è `_STALENESS_MINUTES = 60` (condiviso con le altre surface): adeguato per il primo slice.
- La UI legge freshness da `/sync/freshness/produzioni` (endpoint dedicato, separato da `/sync/freshness/produzione` che serve articoli).

### Limiti noti

- Nessun scheduler automatico (fuori scope).
- La concorrenza è gestita in-memory (single-process); adeguato per deployment attuale.

### Follow-up suggeriti

- Modifica del flag `forza_completata` dalla UI (endpoint backend già disponibile da TASK-V2-030).
- Filtri per bucket/stato nella lista produzioni.
- Test HTTP dedicati per i nuovi endpoint sync/freshness.
