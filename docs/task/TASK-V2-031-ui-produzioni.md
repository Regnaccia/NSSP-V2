# TASK-V2-031 - UI produzioni

## Status
Completed

## Date
2026-04-08

## Scope

Implementare la prima surface browser `produzioni` usando lo schema a `2 colonne`:

- lista produzioni a sinistra
- pannello di dettaglio read-only a destra

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/task/TASK-V2-028-sync-produzioni-attive.md`
- `docs/task/TASK-V2-029-sync-produzioni-storiche.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`

## Goal

Tradurre il primo `core produzioni` in una surface browser consultiva, coerente con il pattern UIX a `2 colonne` e senza introdurre ancora azioni di modifica o sync on demand.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-028`
- `TASK-V2-029`
- `TASK-V2-030`

## Context

Con `TASK-V2-030` la V2 introduce il primo `core produzioni`, che espone:

- elenco produzioni unificato
- `bucket = active | historical`
- `stato_produzione`
- `forza_completata`

Questo task deve tradurre quel contratto nella prima surface browser `produzioni`.

Nel primo slice UI:

- la colonna sinistra mostra le produzioni aggregate
- la colonna destra mostra il dettaglio read-only
- nessun campo e modificabile

## In Scope

- route/surface browser `produzioni`
- layout persistente a `2 colonne` coerente con `UIX_SPEC_PRODUZIONI`
- consumo dei read model Core introdotti da `TASK-V2-030`
- lista produzioni a sinistra con indicatori minimi:
  - cliente destinatario
  - codice articolo
  - numero documento / riga
  - bucket
  - stato produzione
- selezione produzione -> caricamento dettaglio a destra
- pannello di dettaglio read-only con:
  - campi anagrafici rilevanti
  - bucket
  - stato_produzione
  - forza_completata

## Out of Scope

- modifica del flag `forza_completata`
- filtri avanzati per `bucket` o `stato`
- sync on demand `produzioni`
- scheduler
- accesso diretto ai target `sync_*`

## Constraints

- la UI deve consumare solo contratti backend/Core, non mirror sync
- la colonna sinistra deve essere scrollabile in modo indipendente
- `bucket` e `stato_produzione` devono essere dati letti dal backend, non ricalcolati nel frontend
- il task non deve introdurre logica di dominio o join nel frontend

## Acceptance Criteria

- esiste una route/surface browser `produzioni` integrata nel layout applicativo
- la colonna sinistra mostra una lista consultabile delle produzioni
- la selezione di una produzione popola il pannello di destra
- il pannello di destra mostra in sola lettura:
  - dati principali della produzione
  - `bucket`
  - `stato_produzione`
  - `forza_completata`
- la UI gestisce correttamente lo stato vuoto quando nessuna produzione e selezionata
- `npm run build` passa senza errori

## Deliverables

- componenti frontend della surface `produzioni`
- integrazione route/navigation nel layout esistente
- eventuali test frontend o smoke test coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

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
- route/componenti introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Creati:**
- `frontend/src/pages/surfaces/ProduzioniPage.tsx` — surface 2 colonne read-only

**Modificati:**
- `frontend/src/types/api.ts` — aggiunta interfaccia `ProduzioneItem`
- `frontend/src/App.tsx` — route `/produzione/produzioni` + import `ProduzioniPage`
- `frontend/src/components/AppShell.tsx` — voce nav "Produzioni" in `SURFACE_FUNCTIONS.produzione`

### Route/componenti introdotti

- Route: `GET /produzione/produzioni` → `ProduzioniPage`
- `ProduzioniPage` — orchestratore principale; carica lista da backend, gestisce selezione
- `ColonnaLista` — colonna sinistra scrollabile: lista produzioni con `BucketBadge` e `StatoBadge`
- `ColonnaDettaglio` — colonna destra read-only: dettaglio produzione selezionata
- `BucketBadge` — badge blue ("Attiva") / gray ("Storica") per il bucket
- `StatoBadge` — badge green ("Completata") / amber ("Attiva") per stato_produzione
- `RigaInfo` — helper per campi label+valore read-only
- `SelectionKey` — tipo locale `${id_dettaglio}:${bucket}` per disambiguare record con stesso id_dettaglio da bucket diversi

### Scelte di implementazione

- **Nessuna fetch separata per il dettaglio**: `ProduzioneItem` contiene già tutti i campi necessari al pannello di destra — una sola chiamata `GET /produzione/produzioni` popola entrambe le colonne.
- **Selezione toggle**: click sulla stessa produzione la deseleziona (coerente con ProduzioneHome).
- **forza_completata**: mostrato come badge "Forza completata" solo quando `true` (non azione nel primo slice).
- **bucket="active" → label "Attiva"** (riferita al bucket, non allo stato_produzione per evitare ambiguità visiva distinguiamo con colori diversi).

### Test eseguiti

- `npm run build` → ✓ (build pulita, 0 errori TypeScript)
- `python -m pytest tests -q` → 307/307 passed

### Test non eseguiti

- Test frontend E2E: non inclusi in questo task (fuori scope per il primo slice UI).

### Assunzioni

- La chiave di selezione `(id_dettaglio, bucket)` è globalmente unica nella risposta del backend (garantito dal contratto Core).
- Il backend espone `bucket` come stringa letterale `"active"` / `"historical"` — il tipo TypeScript lo riflette.
- Nessun dato di produzione viene ricalcolato nel frontend (bucket, stato_produzione derivano sempre dal backend).

### Limiti noti

- Nessun filtro/ricerca nella lista: adeguato per il primo slice; da introdurre in task successivi se il volume di produzioni lo richiede.
- Nessun sync on demand produzioni: fuori scope in questo task.
- `forza_completata` non è modificabile dalla UI nel primo slice.

### Follow-up suggeriti

- Filtri per bucket (`active` / `historical`) e stato (`attiva` / `completata`).
- Modifica del flag `forza_completata` dalla UI (PATCH endpoint già esistente nel backend).
- Sync on demand produzioni: trigger dalla UI (FreshnessBar + bottone Aggiorna).
- Paginazione della lista se il volume lo richiede.
