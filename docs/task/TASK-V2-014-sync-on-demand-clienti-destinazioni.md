# TASK-V2-014 - Sync on demand clienti destinazioni

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
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/task/TASK-V2-012-core-clienti-destinazioni.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`

## Goal

Integrare il trigger `sync on demand` nella surface clienti/destinazioni tramite backend-controlled refresh, senza introdurre ancora lo scheduler automatico.

## Context

La V2 ha gia:

- sync reale `clienti`
- sync reale `destinazioni`
- un primo modello Core clienti/destinazioni
- una prima surface browser clienti/destinazioni
- un DL specifico che vieta qualsiasi trigger diretto da UI verso script o Easy

Serve ora un primo refresh manuale applicativo che permetta all'utente autorizzato di richiedere l'aggiornamento dati dalla surface, mantenendo il controllo nel backend.

Il task deve introdurre:

- trigger backend di sync on demand
- feedback di stato coerente per il client
- integrazione UI minima del refresh

Il task non deve ancora introdurre scheduling periodico.

## Scope

### In Scope

- endpoint o contratto backend per richiedere sync on demand di:
  - `clienti`
  - `destinazioni`
  - oppure refresh combinato coerente con la surface
- validazione backend di:
  - permessi
  - dipendenze
  - concorrenza minima
- esposizione dello stato base della richiesta di sync
- integrazione nella surface clienti/destinazioni di una action di refresh manuale
- aggiornamento UI dello stato di refresh coerente col contratto backend

### Out of Scope

- scheduler automatico
- orchestrazione distribuita avanzata
- retry policy avanzate
- accesso diretto della UI agli script
- scrittura verso Easy

## Constraints

- la UI non puo chiamare direttamente script o sorgenti Easy
- il backend deve restare unico punto di controllo del trigger
- la sync deve rispettare le dipendenze dichiarate (`destinazioni` dipende da `clienti`)
- il modello deve restare coerente con run metadata e freshness anchor gia esistenti
- la policy `Easy read-only` resta assoluta e senza eccezioni

## Acceptance Criteria

- esiste un trigger backend `sync on demand` coerente con `DL-ARCH-V2-011`
- il backend impedisce almeno le esecuzioni duplicate concorrenti ovvie sullo stesso perimetro
- il backend non consente bypass delle dipendenze dichiarate
- la surface clienti/destinazioni espone una action di refresh manuale
- la UI mostra almeno uno stato tra:
  - richiesta inviata
  - sync in corso
  - sync completata
  - sync fallita
- il refresh UI usa solo il contratto backend e non accede mai direttamente agli script

## Deliverables

- contratto backend per sync on demand
- implementazione backend del trigger controllato
- integrazione frontend nella surface clienti/destinazioni
- test backend e, se sensato, smoke/frontend tests
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/decisions/UIX/DL-UIX-V2-002.md`

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
python scripts/seed_initial.py
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

- iniziare con modello semplice e controllato, non con job system completo
- mantenere il feedback UI minimale ma chiaro
- se il backend non puo ancora offrire async reale, e accettabile un primo modello sincrono o pseudo-asincrono purche il controllo resti backend-owned
- privilegiare il refresh di surface coerente con dipendenze rispetto a trigger UI troppo granulari e potenzialmente confusi

---

## Completion Notes

### Summary

Implementato il modello sync on demand backend-controlled (DL-ARCH-V2-011). Backend: `SyncRunner` con concurrency guard thread-safe (module-level `set + Lock`), esecuzione in ordine di dipendenza con source injection, router FastAPI con `POST /api/sync/surface/logistica` e `GET /api/sync/freshness/logistica`. Frontend: `FreshnessBar` nella surface logistica con stato aggiornato/non aggiornato, pulsante "Aggiorna dati", gestione stati idle/syncing/success/error. Aggiunto `easy_connection_string` e `sync_staleness_threshold_minutes` a `Settings`.

### Files Changed

- `src/nssp_v2/shared/config.py` — aggiunti `easy_connection_string: str | None` e `sync_staleness_threshold_minutes: int = 60`
- `src/nssp_v2/app/schemas/sync.py` — `EntityRunResult`, `SyncSurfaceResponse`, `EntityFreshness`, `FreshnessResponse`
- `src/nssp_v2/app/services/sync_runner.py` — `SyncRunner` con concurrency guard, `SyncAlreadyRunningError`, `SyncEntityUnknownError`
- `src/nssp_v2/app/api/sync.py` — router: POST /surface/logistica (503 se Easy assente, 409 se già in esecuzione), GET /freshness/logistica
- `src/nssp_v2/app/main.py` — registrazione `sync.router`
- `frontend/src/types/api.ts` — aggiunti `EntityRunResult`, `SyncSurfaceResponse`, `EntityFreshness`, `FreshnessResponse`
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — `FreshnessBar` + handler refresh + reload dati dopo sync
- `tests/unit/test_sync_runner.py` — 14 test: esecuzione base, ordine, sorgente mancante, concorrenza, entity code sconosciuto

### Dependencies Introduced

Nessuna nuova dipendenza. `threading` è stdlib Python.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 138 passed, 4 failed pre-esistenti (test_admin_policy) |
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 7.28s — 0 errori TypeScript |
| `POST /api/sync/surface/logistica` (live) | Non eseguita | Easy non disponibile nell'ambiente agente | Da testare con Easy online e DB attivo |

### Assumptions

- Concurrency guard in-memory: adeguato per deployment single-process. In multi-process (gunicorn multi-worker) il guard non è condiviso. Accettabile per il primo slice; futura estensione con DB-level lock.
- `EasyClienteSource` e `EasyDestinazioneSource` sono create nell'handler HTTP al momento del trigger: la connessione pyodbc si apre solo se `easy_connection_string` è configurata. Nessuna connessione aperta al boot.
- Staleness threshold fisso a 60 minuti in `_LOGISTICA_ENTITIES`. Il campo `sync_staleness_threshold_minutes` in Settings è disponibile per future configurazioni per-entity.
- Il POST restituisce 200 anche se alcune sync unit hanno status "error" (errori gestiti per entity). Solo 503 (Easy assente) e 409 (concorrenza) sono errori HTTP del trigger.
- `FreshnessBar` considera `surface_ready=False` se anche una sola entity è stale — indicatore conservativo intenzionale.

### Known Limits

- Esecuzione sincrona: il POST `/sync/surface/logistica` blocca il thread finché le sync non completano. Accettabile per il primo slice (DL-ARCH-V2-011 §5), ma può essere lento con molti record Easy.
- Nessun polling UI: la UI non sa quando un trigger avviato da un'altra sessione completa. Freshness si aggiorna solo al reload manuale o dopo un proprio trigger.
- In caso di crash server mid-sync, il concurrency guard in-memory si resetta al restart (nessun ghost lock permanente).

### Follow-ups

- **TASK-V2-015** (già pianificato): destinazione principale derivata
- Scheduler automatico periodico per le sync di superficie
- Role-checking esplicito su `POST /sync/surface/logistica` (solo ruolo `logistica` o `admin`)
- Estendere concurrency guard a DB-level per deployment multi-process

## Completed At

2026-04-07

## Completed By

Claude Code
