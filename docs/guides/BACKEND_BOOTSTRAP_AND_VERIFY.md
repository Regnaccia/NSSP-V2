# Backend — Bootstrap e verifica

Questa guida permette di installare e verificare il backend V2 in un ambiente
pulito, senza dipendere da stato precedente.

Aggiornata dopo: TASK-V2-004 (auth browser, JWT, bcrypt).

---

## Prerequisiti

- Python 3.11 o superiore
- pip disponibile nell'ambiente
- Docker (per il bootstrap del DB locale)
- Node.js 18+ (per il frontend — opzionale per il solo backend)

---

## 1. Bootstrap Python

Tutti i comandi vanno eseguiti dalla cartella `backend/`.

```bash
cd backend

# Creare il virtual environment
python -m venv .venv

# Attivare il virtual environment
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Installare le dipendenze (incluse quelle di sviluppo)
pip install -e ".[dev]"
```

---

## 2. Configurazione ambiente

```bash
cd backend
cp .env.example .env
```

Variabili principali:

| Variabile            | Default                                                      | Note                                        |
|----------------------|--------------------------------------------------------------|---------------------------------------------|
| `DATABASE_URL`       | `postgresql://postgres:postgres@localhost:5432/nssp_v2`      | Sviluppo — richiesta per Alembic e server   |
| `DATABASE_URL_TEST`  | `postgresql://postgres:postgres@localhost:5432/nssp_v2_test` | Test — database separato                    |
| `APP_ENV`            | `development`                                                |                                             |
| `DEBUG`              | `false`                                                      |                                             |
| `JWT_SECRET_KEY`     | `change-me-in-production`                                    | **Cambiare obbligatoriamente in produzione** |
| `JWT_ALGORITHM`      | `HS256`                                                      |                                             |
| `JWT_EXPIRE_MINUTES` | `480`                                                        | 8 ore                                       |

---

## 3. Bootstrap database locale

Il database locale viene avviato tramite Docker Compose.

```bash
# Dalla root del repository V2
docker compose -f infra/docker/docker-compose.db.yml up -d
```

Questo avvia PostgreSQL 16 su `localhost:5432` con:
- database: `nssp_v2`
- utente: `postgres`
- password: `postgres`

Per verificare che il container sia attivo:

```bash
docker compose -f infra/docker/docker-compose.db.yml ps
```

Per fermare il database:

```bash
docker compose -f infra/docker/docker-compose.db.yml down
```

---

## 4. Migrazioni Alembic

Richiedono PostgreSQL attivo e `DATABASE_URL` configurata.

```bash
cd backend

# Con venv attivo
alembic upgrade head
```

Output atteso:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 20260407001, access control tables: users, roles, user_roles
```

Per verificare lo stato corrente:

```bash
alembic current
```

---

## 5. Seed iniziale

Richiede PostgreSQL attivo con migrazioni già applicate.

```bash
cd backend

# Con venv attivo
python scripts/seed_initial.py
```

Output atteso:

```
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/nssp_v2

  + ruolo creato: admin
  + ruolo creato: produzione
  + ruolo creato: logistica
  + ruolo creato: magazzino

  + utente creato: admin
  + mapping creato: admin -> admin

Seed completato.
```

Il seed è idempotente: eseguirlo più volte non crea duplicati.

Credenziali default seed:
- username: `admin`
- password: `changeme` — **cambiare prima dell'uso in produzione**

---

## 6. Avvio del server

```bash
cd backend

# Con venv attivo
uvicorn nssp_v2.app.main:app --reload
```

Il server sarà disponibile su `http://localhost:8000`.

Endpoint di sistema:

| Endpoint             | Risposta                        | Auth richiesta |
|----------------------|---------------------------------|----------------|
| `GET /health`        | `{"status": "ok"}`              | No             |
| `GET /ready`         | `{"status": "ready"}`           | No             |
| `POST /api/auth/login` | `LoginResponse` con JWT + profilo sessione | No |
| `GET /api/auth/me`   | `SessionResponse` (profilo corrente) | Sì — Bearer JWT |

Esempio login con curl:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' | python -m json.tool
```

Risposta attesa:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "roles": ["admin"],
  "access_mode": "browser",
  "available_surfaces": [
    {"role": "admin", "path": "/admin", "label": "Admin"}
  ]
}
```

---

## 7. Esecuzione test

```bash
cd backend

# Con venv attivo
pytest tests/unit/ -v
```

Output atteso (19 test):

```
tests/unit/test_health.py::test_health_returns_ok                           PASSED
tests/unit/test_health.py::test_ready_returns_ready                         PASSED
tests/unit/test_models_access.py::test_user_table_name                      PASSED
tests/unit/test_models_access.py::test_role_table_name                      PASSED
tests/unit/test_models_access.py::test_user_role_table_name                 PASSED
tests/unit/test_models_access.py::test_user_has_required_columns            PASSED
tests/unit/test_models_access.py::test_role_has_required_columns            PASSED
tests/unit/test_models_access.py::test_user_role_has_required_columns       PASSED
tests/unit/test_models_access.py::test_user_username_is_unique              PASSED
tests/unit/test_models_access.py::test_role_name_is_unique                  PASSED
tests/unit/test_models_access.py::test_user_role_primary_key_is_composite   PASSED
tests/unit/test_security.py::test_hash_password_is_not_plaintext            PASSED
tests/unit/test_security.py::test_verify_password_correct                   PASSED
tests/unit/test_security.py::test_verify_password_wrong                     PASSED
tests/unit/test_security.py::test_create_and_decode_token                   PASSED
tests/unit/test_security.py::test_token_contains_expected_algorithm         PASSED
tests/unit/test_security.py::test_get_available_surfaces_known_roles        PASSED
tests/unit/test_security.py::test_get_available_surfaces_unknown_role_ignored PASSED
tests/unit/test_security.py::test_get_available_surfaces_empty              PASSED

19 passed
```

I test unit non richiedono database attivo.

---

## 8. Verifica strutturale rapida

```bash
cd backend
python -c "from nssp_v2.app.main import app; print('app OK')"
python -c "from nssp_v2.shared.config import settings; print('config OK')"
python -c "from nssp_v2.shared.db import Base; print('db OK')"
python -c "from nssp_v2.app.models.access import User, Role, UserRole; print('models OK')"
python -c "from nssp_v2.shared.security import hash_password, create_access_token; print('security OK')"
python -c "from nssp_v2.app.api.auth import router; print('auth router OK')"
```

---

## 9. Bootstrap frontend

```bash
cd frontend
npm install
npm run dev
```

Il frontend sarà disponibile su `http://localhost:5173`.

Le chiamate `/api/*` vengono proxate automaticamente su `http://localhost:8000` (configurato in `vite.config.ts`).

Per la build di produzione:

```bash
npm run build
```

---

## Sequenza completa da zero (ambiente pulito)

```bash
# 1. Posizionarsi nella root del repository V2

# 2. Avviare PostgreSQL locale
docker compose -f infra/docker/docker-compose.db.yml up -d

# 3. Bootstrap Python
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -e ".[dev]"
cp .env.example .env

# 4. Applicare migrazioni
alembic upgrade head

# 5. Seed iniziale
python scripts/seed_initial.py

# 6. Eseguire i test unit
pytest tests/unit/ -v

# 7. Avviare il server backend
uvicorn nssp_v2.app.main:app --reload

# 8. (Altra finestra) Avviare il frontend
cd ../frontend
npm install
npm run dev
```

Aprire `http://localhost:5173`, effettuare login con `admin` / `changeme`.
