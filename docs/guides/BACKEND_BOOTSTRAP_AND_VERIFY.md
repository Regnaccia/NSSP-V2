# Backend - Bootstrap and Verify

Questa guida permette di installare e verificare il setup V2 in un ambiente pulito.

Stato coperto:

- backend Python
- PostgreSQL locale
- auth browser
- surface `admin`
- sync Easy read-only `clienti`
- sync Easy read-only `destinazioni`
- build frontend

Aggiornata dopo: `TASK-V2-011`.

## Prerequisiti

- Python 3.11+
- pip
- Docker
- Node.js 18+

## 1. Bootstrap Python

Tutti i comandi backend vanno eseguiti da `backend/`.

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev,easy]"
```

`easy` installa il supporto `pyodbc` necessario per schema explorer e sync reali verso Easy.

## 2. Configurazione ambiente

```bash
cd backend
cp .env.example .env
```

Variabili principali:

| Variabile | Default | Note |
|-----------|---------|------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/nssp_v2` | usata da server e Alembic |
| `DATABASE_URL_TEST` | `postgresql://postgres:postgres@localhost:5432/nssp_v2_test` | DB test separato |
| `APP_ENV` | `development` | ambiente applicativo |
| `DEBUG` | `false` | debug flag |
| `JWT_SECRET_KEY` | `change-me-in-production` | da cambiare fuori dal locale |
| `JWT_ALGORITHM` | `HS256` | algoritmo JWT |
| `JWT_EXPIRE_MINUTES` | `480` | 8 ore |
| `EASY_CONNECTION_STRING` | `DRIVER={SQL Server};SERVER=SERVER\SQLEXPRESS;DATABASE=ELFESQL;UID=sa;PWD=CHANGE_ME` | connessione read-only a Easy |

Note:

- se l'ambiente locale contiene variabili incoerenti, il bootstrap puo fallire
- per verifiche riproducibili usare `.env` pulito o env vars esplicite
- `EASY_CONNECTION_STRING` e richiesta solo per schema explorer e sync reali verso Easy
- nessuna scrittura verso Easy e permessa in nessun caso

## 3. Bootstrap database locale

Il DB locale viene avviato con Docker Compose.

```bash
# dalla root del repository V2
docker compose -f infra/docker/docker-compose.db.yml up -d
```

Questo avvia PostgreSQL 16 su `localhost:5432` con:

- database: `nssp_v2`
- user: `postgres`
- password: `postgres`

Verifica rapida:

```bash
docker compose -f infra/docker/docker-compose.db.yml ps
```

Stop:

```bash
docker compose -f infra/docker/docker-compose.db.yml down
```

## 4. Migrazioni Alembic

Richiedono PostgreSQL attivo e `DATABASE_URL` configurata.

```bash
cd backend
alembic upgrade head
```

Stato corrente migration:

```bash
alembic current
```

Le migration attive includono almeno:

- access control (`users`, `roles`, `user_roles`)
- metadati condivisi del layer `sync`
- estensione reale `sync_clienti`
- `sync_destinazioni`

## 5. Seed iniziale

Richiede PostgreSQL attivo e migrazioni gia applicate.

```bash
cd backend
python scripts/seed_initial.py
```

Il seed:

- crea i ruoli iniziali
- crea l'utente `admin`
- collega `admin -> admin`
- e idempotente

Credenziali seed:

- username: `admin`
- password: `changeme`

## 6. Avvio backend

```bash
cd backend
uvicorn nssp_v2.app.main:app --reload
```

Backend disponibile su `http://localhost:8000`.

Endpoint principali:

| Endpoint | Descrizione | Auth |
|----------|-------------|------|
| `GET /health` | health check | No |
| `GET /ready` | ready check | No |
| `POST /api/auth/login` | login browser | No |
| `GET /api/auth/me` | sessione corrente | Bearer JWT |
| `GET /api/admin/users` | lista utenti admin | Bearer JWT admin |
| `POST /api/admin/users` | crea utente | Bearer JWT admin |
| `PATCH /api/admin/users/{id}/active` | attiva/disattiva utente | Bearer JWT admin |
| `PUT /api/admin/users/{id}/roles` | aggiorna ruoli utente | Bearer JWT admin |

Esempio login:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"changeme\"}"
```

Payload atteso:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "roles": ["admin"],
  "access_mode": "browser",
  "available_surfaces": [
    { "role": "admin", "path": "/admin", "label": "Admin" }
  ]
}
```

## 7. Esecuzione test backend

Per la suite unitaria:

```bash
cd backend
pytest tests/unit/ -v
```

La suite copre:

- health endpoints
- modelli access control
- utility security e `available_surfaces`
- policy "ultimo admin attivo"
- contratti sync `clienti` e `destinazioni`

Per l'intera suite:

```bash
cd backend
pytest tests -q
```

## 8. Sync Easy e smoke tecnico

Comandi on demand disponibili:

```bash
cd backend
python scripts/sync_clienti.py --source fake
python scripts/sync_destinazioni.py --source fake
```

Per usare Easy reale:

```bash
cd backend
python scripts/sync_clienti.py
python scripts/sync_destinazioni.py
```

Regole operative:

- `sync_clienti` va eseguita prima di `sync_destinazioni`
- gli script Easy richiedono `EASY_CONNECTION_STRING`
- gli adapter Easy leggono solo `ANACLI` e `POT_DESTDIV`
- gli script scrivono solo sul database interno V2

## 9. Verifica strutturale rapida

```bash
cd backend
python -c "from nssp_v2.app.main import app; print('app OK')"
python -c "from nssp_v2.shared.config import settings; print('config OK')"
python -c "from nssp_v2.shared.db import Base; print('db OK')"
python -c "from nssp_v2.app.models.access import User, Role, UserRole; print('models OK')"
python -c "from nssp_v2.shared.security import hash_password, create_access_token; print('security OK')"
python -c "from nssp_v2.app.api.auth import router; print('auth router OK')"
python -c "from nssp_v2.app.api.admin import router; print('admin router OK')"
python -c "from nssp_v2.sync.models import SyncRunLog, SyncEntityState; print('sync shared OK')"
python -c "from nssp_v2.sync.clienti.unit import ClienteSyncUnit; print('sync clienti OK')"
python -c "from nssp_v2.sync.destinazioni.unit import DestinazioneSyncUnit; print('sync destinazioni OK')"
```

## 10. Bootstrap frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponibile su `http://localhost:5173`.

Build produzione:

```bash
npm run build
```

Le chiamate `/api/*` vengono proxate su `http://localhost:8000`.

## 11. Sequenza completa da zero

```bash
# 1. Posizionarsi nella root V2

# 2. Avviare PostgreSQL
docker compose -f infra/docker/docker-compose.db.yml up -d

# 3. Bootstrap backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
cp .env.example .env

# 4. Migrazioni + seed
alembic upgrade head
python scripts/seed_initial.py

# 5. Test backend e smoke sync locale
pytest tests/unit/ -v
python scripts/sync_clienti.py --source fake
python scripts/sync_destinazioni.py --source fake

# 6. Avviare backend
uvicorn nssp_v2.app.main:app --reload

# 7. Sync reale Easy (solo se EASY_CONNECTION_STRING e configurata)
python scripts/sync_clienti.py
python scripts/sync_destinazioni.py

# 8. In un'altra shell, frontend
cd ../frontend
npm install
npm run build
npm run dev
```

## 12. Smoke flow consigliato

Verifica manuale minima:

1. aprire `http://localhost:5173`
2. effettuare login con `admin` / `changeme`
3. verificare accesso alla surface `admin`
4. verificare presenza lista utenti
5. creare un utente di test
6. assegnare almeno un ruolo
7. verificare visualizzazione delle surfaces derivate
8. eseguire `sync_clienti` e verificare aggiornamento di `sync_clienti`
9. eseguire `sync_destinazioni` e verificare aggiornamento di `sync_destinazioni`
