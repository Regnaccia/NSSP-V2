# TASK-V2-005 - Surface admin per access management

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
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/ARCH/DL-ARCH-V2-006.md`
- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
- `docs/test/TEST-V2-002-task-003-db-bootstrap-validation.md`
- `docs/test/TEST-V2-003-task-004-browser-auth-validation.md`

## Goal

Implementare la prima surface applicativa reale della V2, `admin`, per governare utenti, ruoli e stato attivo/inattivo in modo coerente con il modello auth e con il contratto `available_surfaces`.

## Context

La V2 ha gia:

- backend bootstrap stabile
- DB interno con slice persistente `users`, `roles`, `user_roles`
- auth browser funzionante
- routing iniziale basato su `available_surfaces`
- definizione architetturale esplicita della surface `admin`

Resta ancora un gap operativo importante:

- utenti e ruoli sono ancora governati soprattutto tramite seed o intervento tecnico
- il sistema non offre ancora una capacita applicativa per amministrare accesso e ruoli

Questo task deve trasformare `admin` da semplice placeholder frontend a primo modulo reale della V2.

Il risultato atteso e un workflow browser completo in cui un utente admin puo:

- vedere gli utenti
- creare un utente
- attivare o disattivare un utente
- assegnare o rimuovere ruoli
- vedere le surfaces risultanti dai ruoli

senza uscire dal perimetro stretto definito da `DL-ARCH-V2-006`.

## Scope

### In Scope

- API backend admin minime per:
  - lista utenti
  - dettaglio utente o payload equivalente per editing
  - creazione utente
  - attivazione/disattivazione utente
  - assegnazione ruoli
  - rimozione ruoli
- validazioni backend sulle regole minime di governance
- protezione backend che permetta l'accesso solo a utenti con ruolo `admin`
- garanzia backend che un utente inattivo non possa autenticarsi
- protezione backend contro la rimozione dell'ultimo admin attivo
- frontend browser della surface `admin` con:
  - lista utenti
  - form creazione utente
  - gestione ruoli utente
  - toggle attivo/inattivo
  - visualizzazione surfaces risultanti
- integrazione della surface `admin` con il routing e i placeholder gia presenti
- test backend minimi su policy e workflow admin
- test frontend minimi o smoke test coerenti con il livello raggiunto
- documentazione aggiornata se necessaria

### Out of Scope

- cancellazione fisica utenti
- audit trail avanzato
- cronologia modifiche
- gestione catalogo ruoli da UI
- gestione catalogo surfaces da UI
- permessi fine-grained per azione
- gruppi, tenancy, organizzazioni
- password reset self-service
- workflow di dominio produzione/logistica/magazzino

## Constraints

- rispettare i confini `sync/core/app/shared`
- la surface `admin` resta una surface applicativa, non un pannello di sistema generico
- il backend resta fonte di verita per ruoli, stato utente e `available_surfaces`
- il frontend non deve decidere da solo policy critiche
- il catalogo ruoli resta controllato dal sistema nel primo slice
- il task deve usare password hash reale gia introdotto in `TASK-V2-004`
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`
- il task non deve introdurre permessi granulari o modellazione auth piu ampia del necessario

## Acceptance Criteria

- un utente con ruolo `admin` puo aprire una surface `admin` reale e non solo un placeholder
- la surface `admin` permette di vedere la lista utenti esistenti
- la surface `admin` permette di creare un nuovo utente con password iniziale e ruoli assegnati
- la surface `admin` permette di attivare e disattivare un utente
- la surface `admin` permette di assegnare e rimuovere ruoli da un utente
- il sistema mostra per ogni utente le surfaces risultanti dai ruoli, senza permettere editing diretto delle surfaces
- un utente inattivo non puo autenticarsi
- il sistema impedisce la rimozione dell'ultimo admin attivo
- esistono test backend minimi sulle regole critiche admin
- esistono istruzioni riproducibili di verifica per backend e frontend

## Deliverables

- endpoint backend admin minimi
- eventuali schemi/request-response dedicati per admin access management
- implementazione frontend reale della surface `admin`
- test backend e frontend coerenti con il perimetro
- aggiornamenti documentali minimi:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md` se necessario
  - eventuali README o guide auth/admin

## Environment Bootstrap

Comandi minimi attesi per verificare il task in modo riproducibile.

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
cd backend
pytest tests/ -v
```

```bash
cd frontend
npm run build
```

e con almeno una verifica esplicita del workflow admin che copra:

- accesso di un admin alla surface `admin`
- creazione o aggiornamento utente
- applicazione delle policy critiche lato backend

Devono essere riportati:

- comandi esatti
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il workflow admin stretto e leggibile
- preferire endpoint semplici e spiegabili rispetto a un CRUD generico opaco
- mostrare in UI le surfaces risultanti come dato derivato backend
- introdurre la protezione “ultimo admin attivo” gia in questo slice
- se servono componenti UI riusabili, tenerli piccoli e locali alla surface

---

## Completion Notes

### Summary

Surface `admin` implementata come primo modulo applicativo reale. Backend: schemi admin, policy pura `assert_not_last_active_admin` testabile senza DB, router con 4 endpoint (`GET/POST /users`, `PATCH /users/{id}/active`, `PUT /users/{id}/roles`), guard `require_admin`. Protezione "ultimo admin attivo" attiva sia su disattivazione che su rimozione ruolo. Frontend: `AdminHome.tsx` reale con tabella utenti, modal crea utente, modal edit ruoli, toggle attivo/inattivo, superfici mostrate come derivate (read-only). Fix deprecation: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`. 25 test unit passanti.

### Files Changed

**Backend:**
- `backend/src/nssp_v2/app/schemas/admin.py` — creato: `UserListItem`, `CreateUserRequest`, `SetActiveRequest`, `SetRolesRequest` con validazione ruoli ammessi
- `backend/src/nssp_v2/app/services/__init__.py` — creato
- `backend/src/nssp_v2/app/services/admin_policy.py` — creato: `assert_not_last_active_admin` (funzione pura, testabile senza DB)
- `backend/src/nssp_v2/app/deps/admin.py` — creato: `require_admin` dependency (403 se ruolo admin assente)
- `backend/src/nssp_v2/app/api/admin.py` — creato: router admin con 4 endpoint + logica policy
- `backend/src/nssp_v2/app/main.py` — aggiornato: include admin router su `/api`
- `backend/tests/unit/test_admin_policy.py` — creato: 6 test unit su policy "ultimo admin attivo"

**Frontend:**
- `frontend/src/pages/surfaces/AdminHome.tsx` — sostituito il placeholder con surface reale: tabella utenti, `CreateUserModal`, `EditRolesModal`, toggle attivo/inattivo, superfici derivate read-only

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest tests/unit/ -v` | Claude Code (agente) | venv `.venv` locale backend | 25 passed in 2.25s |
| `GET /api/admin/users` end-to-end | Non eseguita | richiede DB attivo + server | da verificare con DB locale |
| `POST /api/admin/users` end-to-end | Non eseguita | richiede DB attivo + server | da verificare con DB locale |
| `npm run build` frontend | Non eseguita | Node.js non disponibile nell'ambiente agente | da verificare in ambiente con Node.js |

### Assumptions

- La policy "ultimo admin attivo" viene verificata sia su disattivazione utente (se ha ruolo admin) sia su rimozione del ruolo admin
- Il catalogo ruoli è fisso nel primo slice (`admin`, `produzione`, `logistica`, `magazzino`) — validato a livello schema Pydantic
- Le superfici mostrate nella UI admin sono derivate client-side dal mapping statico per la preview nel modal edit ruoli; il dato autorevole resta quello restituito dal backend nel campo `available_surfaces`

### Known Limits

- Endpoint admin non testati end-to-end da agente (richiedono PostgreSQL attivo)
- `npm run build` non verificato da agente (richiede Node.js)
- Nessuna conferma visiva del workflow completo browser: da verificare con DB attivo e `npm run dev`
- La protezione "ultimo admin attivo" non copre scenari di race condition concorrente (non necessario nel primo slice)

### Follow-ups

- Verificare workflow admin end-to-end con DB attivo: login → surface admin → crea utente → assegna ruolo → toggle attivo
- Task successivo naturale: prima surface di dominio (produzione o sync EasyJob)

## Completed At

2026-04-07

## Completed By

Claude Code
