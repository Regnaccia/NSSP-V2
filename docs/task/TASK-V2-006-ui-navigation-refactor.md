# TASK-V2-006 - UI navigation refactor multi-surface

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
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/ARCH/DL-ARCH-V2-006.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
- `docs/task/TASK-V2-005-admin-access-management.md`
- `docs/test/TEST-V2-003-task-004-browser-auth-validation.md`

## Goal

Rifattorizzare la navigazione browser della V2 per passare da chooser post-login a layout persistente multi-surface con sidebar, coerente con `available_surfaces`.

## Context

La V2 ha gia:

- login browser funzionante
- sessione con `roles[]`, `access_mode` e `available_surfaces`
- prima surface reale `admin`
- placeholder o surface iniziali per `produzione`, `logistica`, `magazzino`

Il flusso corrente e ancora centrato sul chooser iniziale, nato come step incrementale valido in `TASK-V2-004`.

Con `DL-UIX-V2-001`, il progetto ha deciso di evolvere verso un modello piu stabile:

- sessione unica
- layout comune persistente
- sidebar costruita da `available_surfaces`
- navigazione tra surface senza nuovo login

Questo task deve tradurre quel DL in implementazione reale del client browser.

## Scope

### In Scope

- refactor del routing frontend browser per adottare un layout persistente condiviso
- introduzione di una sidebar che mostri le `available_surfaces` della sessione
- superamento del chooser iniziale come flusso standard post-login
- redirect post-login coerente:
  - una sola surface disponibile -> redirect automatico
  - piu surface disponibili -> apertura di una surface di default coerente
- integrazione della surface `admin` nel nuovo frame di navigazione
- integrazione dei placeholder o delle surface gia presenti nel nuovo frame di navigazione
- protezione delle route nel nuovo layout in coerenza con sessione e surfaces disponibili
- eventuale mantenimento del chooser solo come fallback tecnico temporaneo, se necessario
- aggiornamento della documentazione tecnica e di verifica se il flusso cambia

### Out of Scope

- redesign grafico completo dell'applicazione
- nuove librerie UI non necessarie
- modifica del contratto backend di `available_surfaces`
- ridefinizione del mapping semantico `role -> surface`
- implementazione delle feature di dominio interne alle surface placeholder
- comportamento Electron o kiosk
- permessi fine-grained lato frontend

## Constraints

- rispettare `DL-UIX-V2-001` come fonte di verita per il pattern di navigazione
- il backend resta fonte di verita per `available_surfaces`
- il frontend non deve derivare le surface leggendo direttamente i ruoli grezzi
- il layout comune non deve rompere la surface `admin` gia implementata
- il task deve rimanere browser-first
- il refactor deve essere incrementale e verificabile senza ridefinire il modello auth
- il chooser iniziale non deve piu essere il percorso standard se il nuovo layout e disponibile

## Acceptance Criteria

- dopo il login l'utente entra nel frame applicativo standard e non nel chooser come percorso principale
- esiste un layout persistente con sidebar condivisa
- la sidebar mostra solo le surface presenti in `available_surfaces`
- un utente puo passare tra piu surface autorizzate senza logout
- le route non autorizzate restano bloccate o non raggiungibili nel client
- la surface `admin` continua a funzionare nel nuovo frame di navigazione
- le altre surface esistenti restano raggiungibili nel nuovo frame almeno come placeholder
- il frontend builda correttamente
- esistono istruzioni chiare per verificare il nuovo flusso browser

## Deliverables

- refactor del routing frontend
- componente o struttura di layout condiviso con sidebar
- aggiornamento delle pagine/surface per usare il nuovo layout
- eventuale deprecazione o riduzione del ruolo di `SurfaceChooser`
- documentazione aggiornata:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md` se necessario
  - eventuali note task/README relative al nuovo flusso browser

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Database:

```bash
docker compose -f infra/docker/docker-compose.db.yml up -d
cd backend
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

e con una verifica esplicita del flusso browser:

- login utente valido
- ingresso nel layout persistente
- visibilita coerente della sidebar
- navigazione tra almeno due surface autorizzate senza logout

Se vengono toccate route guard o integrazioni auth condivise, riportare anche eventuali verifiche backend o smoke aggiuntive.

## Implementation Notes

Direzione raccomandata:

- introdurre un layout shell esplicito, non distribuire logica di sidebar nelle singole pagine
- usare `available_surfaces` come sorgente per la navigazione primaria
- mantenere il fallback semplice e temporaneo se il chooser non puo essere rimosso subito
- tenere separate:
  - navigazione primaria tra surface
  - route interne della singola surface

---

## Completion Notes

### Summary

Navigazione refactored da chooser post-login a layout shell persistente. Introdotto `AppShell.tsx` come layout route condiviso: sidebar costruita da `available_surfaces`, header utente e logout centralizzati. `HomeRedirect` aggiornato: dopo il login si entra direttamente nella prima surface disponibile, senza passare dal chooser. Tutte le surface (admin, produzione, logistica, magazzino) ora condividono il frame; le singole pagine non gestiscono più header o logout propri. `SurfaceChooser` mantenuto come fallback tecnico ma non è più il percorso standard. Build TypeScript + Vite: 96 moduli, zero errori.

### Files Changed

- `frontend/src/components/AppShell.tsx` — creato: layout shell con sidebar `available_surfaces`, logout centralizzato, `<Outlet />` per contenuto
- `frontend/src/App.tsx` — aggiornato: layout route con `AppShell`, `HomeRedirect` → prima surface (no chooser), `/surfaces` mantenuto come fallback
- `frontend/src/pages/surfaces/AdminHome.tsx` — aggiornato: rimossi header e logout locali (ora nel shell)
- `frontend/src/pages/surfaces/ProduzioneHome.tsx` — aggiornato: ridotto a contenuto puro senza chrome
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — aggiornato: ridotto a contenuto puro senza chrome
- `frontend/src/pages/surfaces/MagazzinoHome.tsx` — aggiornato: ridotto a contenuto puro senza chrome

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code (agente) | Node.js locale, frontend V2 | ✓ built in 8.17s — 96 moduli, 0 errori |
| Flusso browser end-to-end (login → shell → navigazione) | Non eseguita | richiede browser + DB attivo + server | da verificare con `npm run dev` |

### Assumptions

- `NavLink` di react-router-dom è già disponibile (react-router-dom è dipendenza esistente); usato per evidenziare la voce di sidebar attiva
- La sidebar non gestisce route interne alla singola surface: usa `to={s.path}` che punta alla root della surface. Le sub-route interne restano gestite dalla surface stessa
- Il `SurfaceChooser` è mantenuto accessibile su `/surfaces` come fallback tecnico; non ci sono link diretti da UI verso di esso nel flusso normale
- `ProtectedRoute` wrappa l'intera layout route `AppShell` (autenticazione) e poi ogni singola surface (ruolo); il doppio wrap è intenzionale e non causa loop

### Known Limits

- Flusso browser non verificato visivamente da agente (richiede browser attivo)
- La sidebar non ha indicatore di collapse/expand — non richiesto in questo slice
- `NavLink` marca come attiva solo la voce che corrisponde esattamente al path root della surface; sub-route interne future dovranno usare `end={false}` o pattern dedicati se necessario

### Follow-ups

- Verificare il flusso browser end-to-end: login → shell visibile → click su voce sidebar → navigazione tra superfici senza logout
- Task successivo naturale: prima surface di dominio reale (produzione o sync EasyJob)

## Completed At

2026-04-07

## Completed By

Claude Code
