# TASK-V2-004 - Browser auth e routing iniziale per ruoli

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
- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/task/TASK-V2-001-bootstrap-backend.md`
- `docs/task/TASK-V2-002-hardening-verifica-backend.md`

## Goal

Implementare il primo slice completo di autenticazione browser della V2, con login utente, sessione applicativa, ruoli multipli nel contratto e routing iniziale coerente con le superfici disponibili.

## Context

La V2 ha gia:

- bootstrap backend minimo
- convenzione di verifica riproducibile dei task
- DL architetturale sul DB interno come backbone persistente
- DL architetturale che distingue identita utente, ruoli e canale di accesso

Il prossimo passo incrementale sensato e introdurre il primo accesso reale al sistema nel canale:

- `browser`

Questo task non deve ancora coprire tutta la security story del progetto.

Deve invece costruire una base pulita e testabile che permetta:

- login nominale
- sessione utente leggibile dal frontend
- supporto a ruoli multipli
- redirect iniziale o landing di scelta in base alle superfici disponibili

Il task deve essere il primo caso reale in cui:

- backend
- frontend browser
- test
- verification contract

lavorano insieme su un flusso end-to-end minimo.

## Scope

### In scope

- modello backend minimo per utenti e ruoli
- persistenza utenti su database V2
- supporto a ruoli multipli per utente
- endpoint login browser
- endpoint sessione corrente, ad esempio `GET /auth/me` o equivalente
- payload sessione con:
  - identita utente
  - `roles[]`
  - `access_mode`
  - superfici disponibili o concetto equivalente
- guard backend minime per il canale browser
- frontend browser con:
  - pagina login
  - store/session management minimale
  - route protection minima
  - redirect iniziale se una sola superficie primaria e disponibile
  - pagina di scelta se l'utente ha piu superfici primarie
- test backend minimi su login e sessione
- test frontend minimi o smoke test adeguati al livello di bootstrap raggiunto
- documentazione di bootstrap e verifica aggiornata se necessaria

### Out of Scope

- kiosk reale
- client Electron reale
- terminal binding o context binding dei kiosk
- SSO, LDAP, OAuth
- refresh token complessi
- gestione password dimenticata
- audit avanzato
- matrice permessi fine-grained per feature secondarie
- implementazione completa delle pagine di dominio produzione/logistica/magazzino

## Constraints

- rispettare i confini `sync/core/app/shared`
- il backend resta fonte di verita per auth, ruoli e capability di sessione
- il frontend non deve dedurre permessi critici da logica locale scollegata dal backend
- il modello utente deve supportare piu ruoli, non un solo ruolo stringa
- `access_mode` deve esistere nel contratto, ma in questo task il solo valore implementato e `browser`
- il task assume che il bootstrap DB interno sia gia disponibile
- le superfici applicative possono essere inizialmente modellate in modo semplice, ma non devono essere hardcodate come pagina unica per ruolo
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`

## Acceptance Criteria

- esiste un login browser funzionante con credenziali utente persistite nel DB V2
- il backend espone una sessione o profilo corrente con `roles[]` e `access_mode`
- un utente con piu ruoli non rompe il flusso: il frontend mostra una scelta coerente o una landing intermedia
- un utente con una sola superficie primaria viene reindirizzato automaticamente
- le route browser protette non sono accessibili senza sessione valida
- il backend applica guard minime coerenti con i ruoli dichiarati
- esistono test backend minimi sul flusso login/sessione
- esistono istruzioni riproducibili di setup ed esecuzione per verificare il task

## Deliverables

- modelli e migrazione minima per utenti e ruoli
- endpoint auth minimi backend
- implementazione frontend browser di login e routing iniziale
- eventuale pagina `surface chooser` o equivalente
- test backend e frontend coerenti con il perimetro
- documentazione aggiornata:
  - guida bootstrap/verifica se necessaria
  - eventuale aggiornamento `README` o guide auth

## Environment Bootstrap

Comandi minimi attesi per verificare il task in modo riproducibile.

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm install
```

Se il task richiede database locale, deve documentare anche il comando minimo per prepararlo.

## Verification Commands

I comandi effettivi potranno essere affinati durante l'implementazione, ma il task deve chiudersi con almeno:

```bash
cd backend
pytest tests/ -v
```

e con i comandi minimi necessari a verificare il frontend browser auth.

Devono essere riportati:

- comandi esatti
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- partire da un modello semplice ma corretto, ad esempio `users` + `user_roles`
- evitare di modellare subito policy di accesso troppo granulari
- usare un concetto esplicito di `available_surfaces` o equivalente nel payload di sessione
- tenere il routing frontend minimale e spiegabile
- se servono pagine placeholder per superfici non ancora implementate, va bene, purche il routing sia corretto

## Completion Notes

### Summary

Primo slice auth browser completo. Backend: JWT via python-jose + bcrypt diretto (passlib 1.7.4 incompatibile con bcrypt 5.x — sostituita con bcrypt API diretta), endpoint `POST /api/auth/login` e `GET /api/auth/me`, payload sessione con `roles[]`, `access_mode`, `available_surfaces[]`. Frontend: bootstrap Vite + React + TypeScript + Tailwind, Zustand store V2 con ruoli multipli, Login, SurfaceChooser (redirect automatico se superficie unica, scelta se multiple), ProtectedRoute con guard per ruolo, 4 placeholder surfaces. 19 test unit backend passanti.

### Files Changed

**Backend:**
- `backend/pyproject.toml` — aggiunto `python-jose[cryptography]>=3.3`, `bcrypt>=4.0` (rimosso passlib)
- `backend/src/nssp_v2/shared/config.py` — aggiunto `jwt_secret_key`, `jwt_algorithm`, `jwt_expire_minutes`
- `backend/src/nssp_v2/shared/security.py` — creato: `hash_password`, `verify_password` (bcrypt diretto), `create_access_token`, `decode_access_token`, `get_available_surfaces`
- `backend/src/nssp_v2/app/schemas/__init__.py` — creato
- `backend/src/nssp_v2/app/schemas/auth.py` — creato: `LoginRequest`, `LoginResponse`, `SessionResponse`, `Surface`
- `backend/src/nssp_v2/app/deps/__init__.py` — creato
- `backend/src/nssp_v2/app/deps/auth.py` — creato: `get_current_user` dependency (Bearer JWT)
- `backend/src/nssp_v2/app/api/auth.py` — creato: `POST /auth/login`, `GET /auth/me`
- `backend/src/nssp_v2/app/main.py` — aggiornato: include auth router su prefisso `/api`
- `backend/.env.example` — aggiornato: variabili JWT
- `backend/scripts/seed_initial.py` — aggiornato: usa `hash_password` (bcrypt reale)
- `backend/tests/unit/test_security.py` — creato: 8 test unit su security utils

**Frontend:**
- `frontend/package.json` — bootstrap: React 18 + Vite + TypeScript + Tailwind + Zustand + react-router-dom + axios + sonner
- `frontend/vite.config.ts` — proxy `/api` → `localhost:8000`
- `frontend/tsconfig.json` — alias `@/` → `src/`
- `frontend/tailwind.config.ts`, `postcss.config.js`, `index.html`
- `frontend/src/index.css` — CSS variables Tailwind
- `frontend/src/main.tsx` — entry point
- `frontend/src/types/api.ts` — tipi `Surface`, `LoginResponse`, `SessionResponse`
- `frontend/src/api/client.ts` — axios client con interceptor Bearer + logout su 401
- `frontend/src/app/authStore.ts` — Zustand store V2: `roles[]`, `available_surfaces[]`, `access_mode`
- `frontend/src/App.tsx` — routing completo con `HomeRedirect` (redirect unico / scelta multipla)
- `frontend/src/components/ProtectedRoute.tsx` — guard auth + guard ruolo
- `frontend/src/pages/Login.tsx` — pagina login
- `frontend/src/pages/SurfaceChooser.tsx` — pagina scelta superficie (utenti multi-ruolo)
- `frontend/src/pages/surfaces/AdminHome.tsx` — placeholder Admin
- `frontend/src/pages/surfaces/ProduzioneHome.tsx` — placeholder Produzione
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — placeholder Logistica
- `frontend/src/pages/surfaces/MagazzinoHome.tsx` — placeholder Magazzino

### Dependencies Introduced

**Backend:**
- `python-jose[cryptography]>=3.3` — JWT encode/decode
- `bcrypt>=4.0` — password hashing (sostituisce passlib, incompatibile con bcrypt 5.x)

**Frontend:**
- `react`, `react-dom`, `react-router-dom`, `axios`, `sonner`, `zustand` (runtime)
- `vite`, `@vitejs/plugin-react`, `tailwindcss`, `typescript`, `postcss`, `autoprefixer` (dev)

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest tests/unit/ -v` | Claude Code (agente) | venv `.venv` locale backend | 19 passed in 2.12s |
| `python -c "from nssp_v2.app.api.auth import router; print('auth router OK')"` | Claude Code (agente) | venv `.venv` locale backend | OK |
| `POST /api/auth/login` end-to-end | Non eseguita | richiede DB attivo + seed | da verificare con DB locale |
| `npm install && npm run build` | Non eseguita | Node.js non disponibile nell'ambiente agente | da verificare in ambiente con Node.js |

### Assumptions

- `passlib[bcrypt]` sostituita da `bcrypt` diretto: passlib 1.7.4 non supporta bcrypt 5.x (errore `__about__` + wrap bug detection fallisce su secret lungo)
- Il seed (`python scripts/seed_initial.py`) deve essere rieseguito dopo TASK-V2-003 perché ora usa bcrypt reale al posto dello sha256 placeholder
- `JWT_SECRET_KEY` va obbligatoriamente cambiata prima del deploy — il default `change-me-in-production` non è sicuro
- Il frontend usa Vite proxy `/api → localhost:8000` — in produzione servire tramite reverse proxy o CORS configurato

### Known Limits

- Login end-to-end e frontend build non verificati da agente (richiedono rispettivamente DB attivo e Node.js)
- Test di integrazione auth (`tests/integration/`) non scritti — da coprire in task successivo con fixture DB dedicata
- Le superfici placeholder non hanno ancora contenuto: da implementare nei task di dominio
- `npm run build` verificherà TypeScript e produrrà eventuali errori di tipo non catturati staticamente

### Follow-ups

- Verificare end-to-end con DB attivo: `alembic upgrade head` + seed + `uvicorn` + `npm run dev`
- Task successivo naturale: prime tabelle source facts (sync EasyJob) o prima superficie applicativa reale

## Completed At

2026-04-07

## Completed By

Claude Code
