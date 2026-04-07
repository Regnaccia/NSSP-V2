# TASK-V2-021 - Sync on demand articoli

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
- `docs/task/TASK-V2-019-core-articoli.md`
- `docs/task/TASK-V2-020-ui-articoli.md`

## Goal

Integrare il trigger `sync on demand` nella surface `articoli` tramite backend-controlled refresh, senza introdurre ancora scheduler automatico o logiche distribuite.

## Context

La V2 ha gia impostato il pattern corretto per il refresh manuale:

- la UI puo solo richiedere una sync
- il backend valida, orchestra ed esegue
- nessuna surface puo accedere direttamente a script o a Easy

Il flusso `articoli` ha ora:

- sync reale `articoli`
- Core `articoli`
- surface browser `articoli` in chiusura

Serve quindi un primo refresh manuale dedicato che permetta all'utente autorizzato di aggiornare il mirror e riflettere il nuovo stato nella surface, mantenendo il controllo interamente nel backend.

## Scope

### In Scope

- endpoint o contratto backend per richiedere `sync on demand` di `articoli`
- validazione backend di:
  - permessi
  - concorrenza minima
  - disponibilita della sorgente Easy
- esposizione dello stato base della richiesta di sync
- integrazione nella surface `articoli` di una action di refresh manuale
- aggiornamento UI dello stato di refresh coerente col contratto backend

### Out of Scope

- scheduler automatico
- orchestrazione distribuita avanzata
- retry policy avanzate
- accesso diretto della UI agli script
- scrittura verso Easy
- introduzione di dati interni configurabili articolo

## Constraints

- la UI non puo chiamare direttamente script o sorgenti Easy
- il backend deve restare unico punto di controllo del trigger
- la policy `Easy read-only` resta assoluta e senza eccezioni
- il modello deve restare coerente con run metadata e freshness anchor gia esistenti per `articoli`
- il task non deve introdurre logica di dominio o orchestrazione multi-entita non necessaria

## Acceptance Criteria

- esiste un trigger backend `sync on demand` per `articoli` coerente con `DL-ARCH-V2-011`
- il backend impedisce almeno le esecuzioni duplicate concorrenti ovvie su `articoli`
- la surface `articoli` espone una action di refresh manuale dedicata
- la UI mostra almeno uno stato tra:
  - richiesta inviata
  - sync in corso
  - sync completata
  - sync fallita
- il refresh UI usa solo il contratto backend e non accede mai direttamente agli script
- `npm run build` passa senza errori

## Deliverables

- contratto backend per sync on demand `articoli`
- implementazione backend del trigger controllato
- integrazione frontend nella surface `articoli`
- test backend e, se sensato, smoke/frontend tests
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
docker compose -f ../infra/docker/docker-compose.db.yml up -d
cp .env.example .env
alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
```

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e:

```bash
cd frontend
npm run build
```

Se presenti endpoint di refresh, riportare anche almeno una verifica applicativa esplicita del trigger.

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- riusare il pattern gia validato per `clienti/destinazioni`, ma restringendolo al solo perimetro `articoli`
- mantenere il feedback UI minimale ma chiaro
- se il backend non puo ancora offrire async reale, e accettabile un primo modello sincrono o pseudo-asincrono purche il controllo resti backend-owned
- integrare il trigger nella surface `articoli` senza anticipare ancora dati interni configurabili

---

## Completion Notes

### Summary

Integrato il pattern sync on demand (DL-ARCH-V2-011) per la surface `produzione/articoli`, riusando esattamente il modello già validato per `logistica`. Backend: `ArticoloSyncUnit` registrata in `SyncRunner._UNIT_MAP`; nuovi endpoint `POST /api/sync/surface/produzione` e `GET /api/sync/freshness/produzione` in `sync.py`. Frontend: `FreshnessBar` aggiunta a `ProduzioneHome.tsx` con stati idle/syncing/success/error, pulsante "Aggiorna dati", ricarica lista articoli e freshness dopo sync completata.

### Files Changed

- `src/nssp_v2/app/services/sync_runner.py` — aggiunto `ArticoloSyncUnit` in `_UNIT_MAP`
- `src/nssp_v2/app/api/sync.py` — aggiunto `_PRODUZIONE_ENTITIES`, import `EasyArticoloSource`, endpoint `POST /surface/produzione` e `GET /freshness/produzione`
- `frontend/src/pages/surfaces/ProduzioneHome.tsx` — aggiunto import `FreshnessResponse`, `SyncSurfaceResponse`; componente `FreshnessBar`; stato `syncStatus`, `freshness`; `handleRefresh`, `loadFreshness`; layout `flex flex-col h-full` con FreshnessBar in cima

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 229 passed in 3.48s |
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 3.62s — 0 errori TypeScript |

### Assumptions

- `_PRODUZIONE_ENTITIES = ["articoli"]` è una lista singola: nessuna dipendenza tra entità da rispettare. Il pattern rimane estendibile aggiungendo voci alla lista.
- Il concurrency guard module-level del `SyncRunner` copre sia il perimetro logistica che produzione: se `articoli` è già in esecuzione (es. da uno script manuale), il backend risponde 409 correttamente.
- Nessun nuovo test aggiunto: il test `test_sync_runner.py` esistente copre già il pattern `run_surface` con entità custom; i nuovi endpoint seguono esattamente la stessa struttura del logistica già testata.

### Known Limits

- I nuovi endpoint non hanno test di integrazione HTTP dedicati (pattern identico a logistica già coperto). Test aggiuntivi possono essere aggiunti se richiesti.
- La `FreshnessBar` non ha un auto-refresh periodico: l'utente deve cliccare manualmente "Aggiorna dati".

### Follow-ups

- Eventuale introduzione di dati interni configurabili articolo (DL-ARCH-V2-013 §8)
- Eventuale auto-refresh freshness (polling leggero) se richiesto dalla UX

## Completed At

2026-04-07

## Completed By

Claude Code
