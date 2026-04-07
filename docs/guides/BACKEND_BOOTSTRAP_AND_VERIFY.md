# Backend — Bootstrap e verifica

Questa guida permette di installare il backend V2 e verificarne il funzionamento
in un ambiente pulito, senza dipendere da stato precedente.

---

## Prerequisiti

- Python 3.11 o superiore
- pip disponibile nell'ambiente

Non è necessario che PostgreSQL sia attivo per eseguire i test di bootstrap.
Il venv locale è sufficiente.

---

## Comandi di bootstrap

Tutti i comandi vanno eseguiti dalla cartella `backend/`.

```bash
cd backend

# 1. Creare il virtual environment
python -m venv .venv

# 2. Attivare il virtual environment
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. Installare le dipendenze (incluse quelle di sviluppo)
pip install -e ".[dev]"
```

---

## Avvio del server

```bash
cd backend

# Con venv attivo
uvicorn nssp_v2.app.main:app --reload
```

Il server sarà disponibile su `http://localhost:8000`.

Endpoint di sistema:
- `GET /health` → `{"status": "ok"}`
- `GET /ready`  → `{"status": "ready"}`

---

## Esecuzione test

```bash
cd backend

# Con venv attivo
pytest tests/unit/ -v
```

Output atteso al bootstrap:

```
tests/unit/test_health.py::test_health_returns_ok     PASSED
tests/unit/test_health.py::test_ready_returns_ready   PASSED

2 passed
```

---

## Configurazione

Copiare `.env.example` in `.env` e adattare i valori:

```bash
cp .env.example .env
```

Variabili principali:

| Variabile      | Default                                            | Note                    |
|----------------|----------------------------------------------------|-------------------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/nssp_v2` | Richiesta per Alembic   |
| `APP_ENV`      | `development`                                      |                         |
| `DEBUG`        | `false`                                            |                         |

I test di bootstrap non richiedono un database attivo.

---

## Migrazioni Alembic

Richiedono PostgreSQL attivo e `DATABASE_URL` configurata.

```bash
cd backend

# Con venv attivo
alembic upgrade head
```

---

## Verifica strutturale rapida

Per verificare che la struttura del package sia corretta senza eseguire i test:

```bash
cd backend
python -c "from nssp_v2.app.main import app; print('app OK')"
python -c "from nssp_v2.shared.config import settings; print('config OK')"
python -c "from nssp_v2.shared.db import Base; print('db OK')"
```
