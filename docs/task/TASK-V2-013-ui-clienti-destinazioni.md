# TASK-V2-013 - UI clienti destinazioni

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
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/task/TASK-V2-012-core-clienti-destinazioni.md`

## Goal

Implementare la prima UI browser della surface clienti/destinazioni usando esclusivamente i read model Core esposti dal backend.

## Context

Con `TASK-V2-012` la V2 introduce il primo slice Core `clienti + destinazioni`.

Questo task deve tradurre quel modello applicativo nella prima surface browser coerente con `DL-UIX-V2-002`:

- colonna sinistra per i clienti
- colonna centrale per le destinazioni del cliente selezionato
- colonna destra per il dettaglio della destinazione selezionata

Il task non deve ancora introdurre il trigger di sync on demand.
La UI deve concentrarsi su navigazione, selezione e presentazione dei dati disponibili.

## Scope

### In Scope

- route/surface browser clienti-destinazioni
- layout persistente a 3 colonne coerente con `DL-UIX-V2-002`
- consumo dei read model Core introdotti da `TASK-V2-012`
- ricerca o filtro minimo clienti
- selezione cliente -> caricamento destinazioni
- selezione destinazione -> caricamento dettaglio
- visualizzazione distinta tra dati Easy read-only e `nickname_destinazione`
- editing minimo di `nickname_destinazione`, se gia esposto dal backend del task 012

### Out of Scope

- trigger sync on demand
- scheduler
- accesso diretto ai target `sync_*`
- nuovi campi Easy non presenti nel Core slice
- configurazioni logistiche oltre `nickname_destinazione`

## Constraints

- la UI deve consumare solo contratti backend/Core, non mirror sync
- il layout deve restare coerente con sidebar e frame applicativo comune
- i dati Easy devono essere mostrati come read-only
- `nickname_destinazione` deve risultare distinto dai dati sincronizzati
- il task non deve introdurre logica di join o fallback dati nel client oltre quella gia prevista dal contratto Core

## Acceptance Criteria

- esiste una route/surface browser clienti-destinazioni integrata nel layout applicativo
- la colonna sinistra mostra i clienti disponibili con filtro minimo
- la colonna centrale mostra le destinazioni del cliente selezionato
- la colonna destra mostra il dettaglio della destinazione selezionata
- la UI gestisce correttamente gli stati vuoti guidati:
  - nessun cliente selezionato
  - nessuna destinazione selezionata
- la UI distingue chiaramente dati Easy read-only e `nickname_destinazione`
- se il backend lo supporta gia, `nickname_destinazione` e modificabile dalla UI senza toccare dati Easy

## Deliverables

- componenti frontend della surface clienti-destinazioni
- integrazione route/navigation nel layout esistente
- eventuali test frontend o smoke test coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/DL-UIX-V2-002.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

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
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- trattare `DL-UIX-V2-002` come target UI del primo slice, ma usare solo i campi realmente disponibili dal Core
- se alcuni campi del DL UIX non sono ancora disponibili nel Core, privilegiare il contratto backend reale e aggiornare la documentazione
- mantenere il layout intenzionale e leggibile, senza ricadere in una tabella annidata unica

---

## Completion Notes

### Summary

Implementata la prima surface browser logistica clienti/destinazioni. Sul backend: nuovo router FastAPI `logistica` (4 endpoint, integrato in `main.py`). Sul frontend: `LogisticaHome.tsx` con layout a 3 colonne (clienti con filtro, destinazioni, dettaglio+nickname). I tipi `ClienteItem`, `DestinazioneItem`, `DestinazioneDetail` sono stati aggiunti a `types/api.ts`. La UI distingue esplicitamente dati Easy read-only dalla sezione "Configurazione interna" per il nickname.

### Files Changed

- `src/nssp_v2/app/api/logistica.py` — nuovo router: GET /clienti, GET /clienti/{id}/destinazioni, GET /destinazioni/{id}, PATCH /destinazioni/{id}/nickname
- `src/nssp_v2/app/main.py` — registrazione `logistica.router` con prefix `/api`
- `frontend/src/types/api.ts` — aggiunti `ClienteItem`, `DestinazioneItem`, `DestinazioneDetail`
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — surface a 3 colonne (sostituisce placeholder)

### Dependencies Introduced

Nessuna nuova dipendenza. Axios, React, Tailwind e Sonner già presenti.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code (agente) | frontend V2 locale, Node, TypeScript 5.7, Vite 6.4 | ✓ built in 7.35s — 0 errori TypeScript |
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 124 passed, 4 failed pre-esistenti (test_admin_policy) — nessuna regressione |

### Assumptions

- Il router logistica non implementa role-checking esplicito sul ruolo `logistica`: l'autenticazione Bearer è sufficiente per questo primo slice; la route nel frontend è già role-protetta da `ProtectedRoute roles={['logistica']}`.
- Il click su un cliente già selezionato deseleziona il cliente (toggle) — comportamento intuitivo per la navigazione.
- Il campo `display_label` è computato dal Core e consumato direttamente senza logica di fallback nel client (DL-ARCH-V2-010 §11).
- La larghezza delle colonne (w-64, w-72) è fissa — sufficiente per il primo slice, regolabile in un task successivo.

### Known Limits

- Altezza colonne non strettamente full-viewport: il layout usa `min-h-full flex` che produce colonne side-by-side ma non garantisce scroll indipendente per colonne molto lunghe (il contenuto scorre come una pagina unica nel container `overflow-auto` di AppShell). Funzionalmente corretto, visivamente raffinabile.
- Nessun test frontend dedicato: la build TypeScript senza errori costituisce la verifica strutturale; test E2E richiedono infrastruttura non ancora presente.
- Nessun trigger sync on demand: la UI mostra i dati disponibili nel DB locale (out of scope per questo task).

### Follow-ups

- **TASK-V2-014**: Sync on-demand trigger dalla surface logistica
- Aggiungere role-checking sul router logistica (middleware o dependency `require_logistica`)
- Migliorare layout altezza colonne con `h-screen overflow-hidden` once AppShell è pronto per supportarlo

## Completed At

2026-04-07

## Completed By

Claude Code
