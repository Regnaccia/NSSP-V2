# TASK-V2-017 - Sidebar navigation contestuale

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
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`

## Goal

Implementare nella sidebar una navigazione contestuale per-surface, in cui la selezione di una surface mostri le funzioni interne dedicate a quella surface.

## Context

La sidebar attuale gestisce gia il livello primario delle surface autorizzate.

Con la crescita delle funzioni di `admin`, `logistica` e future surface, serve un secondo livello di navigazione che mostri le funzioni rilevanti della surface attiva.

Il primo slice puo mantenere questo mapping nel frontend, purche resti coerente con le surface autorizzate dal backend.

## Scope

### In Scope

- introduzione del livello secondario di navigazione contestuale nella sidebar o nel frame equivalente
- mappatura iniziale frontend-defined di:
  - `admin` -> funzioni admin correnti
  - `logistica` -> funzioni logistica correnti
- evidenza chiara della surface attiva
- evidenza chiara della funzione attiva nella surface
- integrazione con il routing esistente

### Out of Scope

- capabilities/menu esposti dal backend
- permessi fini per singola funzione
- redesign completo del sistema di layout
- comportamento kiosk

## Constraints

- la navigazione primaria continua a derivare da `available_surfaces`
- il livello secondario non deve comparire per surface non autorizzate
- il task non deve spostare autorizzazioni dal backend al frontend
- il pattern deve restare estendibile a future funzioni senza riprogettare il frame

## Acceptance Criteria

- selezionando `admin` compaiono le funzioni interne di `admin`
- selezionando `logistica` compaiono le funzioni interne di `logistica`
- la funzione attiva e chiaramente distinguibile nella navigazione contestuale
- il build frontend passa senza errori
- il frame applicativo resta coerente con il layout multi-surface esistente

## Deliverables

- aggiornamenti frontend della sidebar o del frame di navigazione
- configurazione iniziale delle funzioni per-surface
- eventuale aggiornamento di documentazione UIX se necessario

## Environment Bootstrap

Frontend:

```bash
cd frontend
npm install
```

Backend opzionale per smoke reale:

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

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

Se viene fatta verifica manuale, riportare almeno:

- surface testate
- funzioni contestuali visibili
- route attiva verificata

## Implementation Notes

Direzione raccomandata:

- trattare la navigazione contestuale come secondo livello del frame, non come sostituzione della sidebar primaria
- partire con una configurazione semplice e leggibile nel frontend
- evitare nesting eccessivo o menu troppo densi nel primo slice

---

## Completion Notes

### Summary

Implementata la navigazione contestuale a due livelli in `AppShell.tsx` (DL-UIX-V2-003). Il livello primario (surface) era già presente; il livello secondario (funzioni contestuali) è frontend-defined tramite la costante `SURFACE_FUNCTIONS`. Le funzioni contestuali compaiono sotto la surface attiva e restano nascoste per le altre surface. `App.tsx` aggiornato con sub-route esplicite (`/admin/utenti`, `/logistica/clienti-destinazioni`) e redirect dalle root surface alle rispettive prime funzioni.

### Files Changed

- `frontend/src/components/AppShell.tsx` — aggiunta costante `SURFACE_FUNCTIONS`, rilevamento `isActiveSurface` da `useLocation`, rendering livello secondario con `NavLink end` sotto la surface attiva
- `frontend/src/App.tsx` — rimosso wildcard `/*` su admin e logistica; aggiunte route esplicite `/admin/utenti` → `AdminHome` e `/logistica/clienti-destinazioni` → `LogisticaHome`; aggiunti redirect da `/admin` e `/logistica` alle prime funzioni contestuali

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 3.29s — 0 errori TypeScript |

### Assumptions

- Per `admin` e `logistica` la route base (es. `/admin`) redirige immediatamente alla prima funzione contestuale. Questo è il comportamento più prevedibile con una sola funzione per surface.
- `SURFACE_FUNCTIONS` viene interrogata solo per le surface in `available_surfaces`: se un utente non ha la surface `logistica`, le sue funzioni non compaiono nella sidebar (protezione UI complementare alla guard backend).
- Le surface `produzione` e `magazzino` non hanno ancora funzioni contestuali definite: la sidebar le mostra come voci primarie senza livello secondario, che è corretto (nessuna regressione).
- Il NavLink primario su `/admin` usa il default React Router (prefix match, no `end`): sarà attivo anche a `/admin/utenti`. Comportamento desiderato — la surface rimane evidenziata.

### Known Limits

- La `SURFACE_FUNCTIONS` map è hardcoded nel frontend (DL-UIX-V2-003 §3 lo ammette esplicitamente per il primo slice).
- `produzione` e `magazzino` non hanno sub-funzioni definite: le loro route restano come `/*` wildcard (nessun sub-routing specifico). Estendere con le future funzioni seguendo lo stesso pattern.
- Nessuna verifica manuale (solo build). Il wiring routing + sidebar è verificabile visivamente al primo avvio.

### Follow-ups

- valutare futuro allineamento a capabilities backend per funzione
- aggiungere funzioni contestuali a `produzione` e `magazzino` quando disponibili

## Completed At

2026-04-07

## Completed By

Claude Code
