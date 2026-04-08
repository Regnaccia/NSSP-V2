# TASK-V2-035 - Filtri e ricerca produzioni

## Status
Completed

## Date
2026-04-08

## Scope

Raffinare la surface `produzioni` introducendo:

- filtro per `stato_produzione`
- ricerca per `codice articolo`
- ricerca per `numero documento`

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`
- `docs/task/TASK-V2-034-performance-produzioni-active-default.md`

## Goal

Migliorare consultazione e navigabilita della surface `produzioni`, riducendo il rumore in lista e permettendo un accesso piu rapido alle produzioni rilevanti.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-030`
- `TASK-V2-031`

`TASK-V2-034` e fortemente raccomandato, perche il filtro stato e la ricerca devono idealmente poggiare sul nuovo contratto paginato e server-side.

## Context

La surface `produzioni` espone gia:

- `bucket`
- `stato_produzione`
- lista consultiva a `2 colonne`

Il passo successivo naturale e permettere all'utente di:

- vedere solo produzioni `attive`
- vedere solo produzioni `completate`
- cercare rapidamente per articolo o documento

## In Scope

- filtro esplicito per `stato_produzione` con almeno:
  - `all`
  - `attiva`
  - `completata`
- ricerca per:
  - `codice_articolo`
  - `numero_documento`
- integrazione dei filtri nella colonna sinistra della surface `produzioni`
- aggiornamento backend/Core se necessario per supportare i filtri lato server
- aggiornamento della UI per comporre correttamente:
  - filtro `bucket`
  - filtro `stato_produzione`
  - ricerca testuale

## Out of Scope

- ricerca full-text avanzata
- filtri per cliente, date o materiale
- modifica del flag `forza_completata`
- sync on demand

## Constraints

- la UI non deve ricalcolare `stato_produzione`
- la ricerca deve usare solo campi gia esposti dal Core
- se il backend supporta gia filtro/paginazione server-side, anche il filtro `stato_produzione` e la ricerca devono seguire lo stesso modello
- la surface deve restare coerente con la variante UIX a `2 colonne`

## Acceptance Criteria

- la surface `produzioni` permette di filtrare per:
  - `all`
  - `attiva`
  - `completata`
- la surface permette la ricerca per:
  - `codice_articolo`
  - `numero_documento`
- filtri e ricerca si combinano correttamente con la lista esistente
- il dettaglio continua a caricarsi coerentemente sulla produzione selezionata
- `npm run build` passa senza errori

## Deliverables

- aggiornamento backend/Core se richiesto dal contratto
- aggiornamento UI della surface `produzioni`
- eventuali test backend/frontend coerenti
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
- filtri/query introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Modificati backend:**
- `src/nssp_v2/core/produzioni/queries.py` — `list_produzioni` esteso con `stato: str | None` e `q: str | None`; helper `_build_query_attive` e `_build_query_storiche` con LEFT JOIN su `CoreProduzioneOverride` (solo quando `stato` è specificato), filtro WHERE per `stato="attiva"/"completata"`, ricerca `ilike` su `codice_articolo` e `numero_documento`; costante `_VALID_STATI = {"attiva", "completata"}`; validazione con `ValueError`
- `src/nssp_v2/app/api/produzione.py` — endpoint `GET /produzioni` esteso con query params `stato` e `q`
- `tests/core/test_core_produzioni.py` — 13 nuovi test per filtro stato e ricerca (41 totali)

**Modificati frontend:**
- `frontend/src/pages/surfaces/ProduzioniPage.tsx` — aggiunto tipo `StatoFilter` (`'all' | 'attiva' | 'completata'`); stato `stato` + `q` nel componente; `fetchPage` passa `stato` (se != "all") e `q` (se non vuota) come query params; `loadInitial` accetta `b`, `st`, `qVal`; `handleStatoChange` (reset lista); `handleQChange` (debounce 400ms + reset lista); `handleRefresh` e `handleBucketChange` aggiornati; `ColonnaLista` estesa con select stato e input ricerca

### Filtri/query introdotti

- `GET /api/produzione/produzioni?stato=attiva` → solo produzioni non completate
- `GET /api/produzione/produzioni?stato=completata` → solo produzioni completate (incluso override forza_completata)
- `GET /api/produzione/produzioni?q=ART001` → ricerca case-insensitive su codice_articolo e numero_documento
- I filtri `bucket`, `stato` e `q` si combinano con la paginazione esistente

### Test eseguiti

41 test in `tests/core/test_core_produzioni.py`:
- Filtro stato attiva: 2 produzioni, restituisce solo la non completata ✓
- Filtro stato completata: 2 produzioni, restituisce solo la completata ✓
- Filtro stato completata con override forza_completata ✓
- Filtro stato attiva esclude override completata ✓
- Filtro stato su bucket historical ✓
- Stato non valido → ValueError ✓
- Ricerca per codice_articolo ✓
- Ricerca per numero_documento ✓
- Ricerca senza match → 0 risultati ✓
- Ricerca case-insensitive ✓
- Ricerca parziale (contiene) ✓
- Ricerca e stato combinati ✓
- Stringa q vuota o solo spazi → nessun filtro ✓

Suite completa: 330/330 passed.

### Test non eseguiti

- Test HTTP dell'endpoint con i nuovi parametri `stato` e `q`: non inclusi. La logica è coperta dai test unitari sulla query Core.
- Test frontend: non inclusi (fuori scope standard; componente è read-only per i filtri).

### Assunzioni

- `stato` con valore `None` (assente) significa nessun filtro — la UI non passa il parametro quando seleziona "Tutti gli stati".
- Il filtro `stato` lato SQL usa LEFT JOIN con `CoreProduzioneOverride` solo quando `stato` è specificato — evita join inutili nella query non filtrata.
- La ricerca `q` è "contains" case-insensitive su entrambi i campi (OR): un match su uno dei due basta.
- Debounce 400ms sul campo di ricerca per evitare richieste a ogni keystroke.
- Reset offset+lista ad ogni cambio di filtro (bucket, stato, q) — comportamento uguale a `handleBucketChange`.

### Limiti noti

- La ricerca non è full-text (no stemming, no ranking): è una semplice `ILIKE %q%`.
- Il cambio di qualsiasi filtro resetta la selezione corrente nella lista.
- Con bucket="all" e filtri attivi, il conteggio totale è la somma dei conteggi filtrati delle due tabelle; la paginazione lineare è stabile finché l'ordine è deterministico.

### Follow-up suggeriti

- Filtro per cliente (ragione_sociale) — campo già esposto nel read model.
- Virtualizzazione della lista per dataset molto grandi.
- Highlight del testo trovato nella lista quando la ricerca è attiva.
