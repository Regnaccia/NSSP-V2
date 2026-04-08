# TASK-V2-034 - Performance produzioni con default active

## Status
Completed

## Date
2026-04-08

## Scope

Ridurre il costo di caricamento della surface `produzioni` evitando il caricamento iniziale dell'intero storico e introducendo un contratto di query piu controllato.

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`
- `docs/task/TASK-V2-032-sync-on-demand-produzioni.md`
- `docs/task/TASK-V2-033-forza-completata-produzioni.md`

## Goal

Portare la surface `produzioni` a un comportamento piu sostenibile su dataset grandi, trattando lo storico come consultazione esplicita e non come parte del caricamento standard.

## Context

Nel comportamento attuale la vista `produzioni` risulta lenta, con alta probabilita perche il dataset storico e molto ampio.

Il primo correttivo scelto e:

- non mostrare le produzioni storiche di default

La surface deve aprirsi sulle sole produzioni attive, lasciando lo storico disponibile solo tramite filtro esplicito e query backend controllate.

## In Scope

- default della lista `produzioni` su `bucket=active`
- filtro esplicito `bucket` con almeno:
  - `active`
  - `historical`
  - `all`
- filtro `bucket` applicato lato backend/Core
- paginazione backend della lista `produzioni`
- aggiornamento UI per consumare la lista paginata
- caricamento del dettaglio solo per la produzione selezionata

## Out of Scope

- virtualizzazione avanzata frontend
- ricerca full-text avanzata
- scheduler automatico
- modifica della logica di `stato_produzione`
- modifica del flag `forza_completata`

## Constraints

- la UI non deve caricare tutto lo storico in apertura
- il filtro `bucket` non deve essere solo client-side
- la paginazione deve essere backend-driven
- la surface deve restare coerente con la spec UIX `produzioni`

## Acceptance Criteria

- la surface `produzioni` apre di default con sole produzioni `active`
- l'utente puo selezionare esplicitamente:
  - `active`
  - `historical`
  - `all`
- il backend supporta il filtro `bucket`
- il backend supporta paginazione della lista
- la UI consuma la lista paginata senza regressioni funzionali
- il dettaglio continua a caricarsi solo sulla riga selezionata
- `npm run build` passa senza errori

## Deliverables

- estensione query/backend per lista `produzioni`
- contratto API con filtro `bucket` e paginazione
- aggiornamento UI della surface `produzioni`
- eventuali test backend/frontend coerenti col task
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
- estensioni del contratto query/API
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Modificati backend:**
- `src/nssp_v2/core/produzioni/read_models.py` — aggiunto `ProduzioniPaginata` (items, total, limit, offset)
- `src/nssp_v2/core/produzioni/queries.py` — `list_produzioni` ora accetta `bucket`, `limit`, `offset`; restituisce `ProduzioniPaginata`; helper `_load_overrides`, `_load_overrides_storica` (carica override solo per le righe della pagina corrente, non tutti); costanti `_DEFAULT_LIMIT=50`, `_MAX_LIMIT=200`
- `src/nssp_v2/core/produzioni/__init__.py` — esporta `ProduzioniPaginata`
- `src/nssp_v2/app/api/produzione.py` — endpoint `GET /produzioni` aggiornato con query params `bucket`, `limit`, `offset`; import `ProduzioniPaginata`
- `tests/core/test_core_produzioni.py` — aggiornato per il nuovo contratto (`.items`); 10 nuovi test per filtro e paginazione (28 totali)

**Modificati frontend:**
- `frontend/src/types/api.ts` — aggiunta interfaccia `ProduzioniPaginata`
- `frontend/src/pages/surfaces/ProduzioniPage.tsx` — bucket selector (active/historical/all, default active), stato `total`+`offset`, logica `fetchPage` (append/reset), pulsante "Carica altri N rimanenti", `handleBucketChange` (reset lista + selezione), rimozione del `useEffect` su `detail?.codice_articolo` (rimpiazzato con `useRef` per reset `saveStatus`)

### Estensioni del contratto query/API

- `GET /api/produzione/produzioni?bucket=active&limit=50&offset=0` → `ProduzioniPaginata`
- `bucket`: "active" (default) | "historical" | "all"; 422 se non valido
- `limit`: 1–200, clamped; default 50
- `offset`: ≥0; default 0
- Per bucket="all": attive prima (offset/limit applicato linearmente sulle due tabelle)

### Test eseguiti

28 test in `tests/core/test_core_produzioni.py`:
- Bucket: active, historical, all, default active, esclusione, bucket non valido ✓
- Stato: regola standard, quantita None, storica completata ✓
- forza_completata: override, precedenza, reset, isolamento bucket ✓
- Inattivi esclusi ✓
- Paginazione: limit, offset, offset oltre totale, "all" attraversa buckets, "all" solo storiche, limit clamp ✓

Suite completa: 317/317 passed.

### Test non eseguiti

- Test HTTP dell'endpoint paginato: non inclusi. La logica di paginazione è coperta dai test unitari sulla query Core.

### Assunzioni

- `_MAX_LIMIT = 200`: limite ragionevole per evitare risposte troppo grandi; configurabile in futuro.
- Per bucket="all" la paginazione è lineare: le attive occupano i primi `count_a` slot, le storiche i successivi. Questo è stabile finché l'ordine di entrambe le query è deterministico (id_dettaglio ASC).
- Gli override sono caricati filtrati per le sole righe della pagina (`IN` query) invece che per tutti — riduce il volume di dati caricato per ogni pagina.

### Limiti noti

- Nessuna ricerca full-text (fuori scope).
- La paginazione "all" con offset che cade esattamente sul confine attive/storiche è gestita correttamente dal codice.
- Il cambio bucket resetta la selezione corrente nella lista.

### Follow-up suggeriti

- Ricerca testo nella lista (filtro client-side sugli item già caricati, o query backend con parametro `q`).
- Filtro per `stato_produzione` (attiva/completata) lato backend.
- Virtualizzazione della lista se il numero di item caricati diventa molto grande.
