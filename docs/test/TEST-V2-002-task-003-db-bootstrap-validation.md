# TEST-V2-002 - Verifica TASK-V2-003 bootstrap DB interno

## Date
2026-04-07

## Scope

Verifica del task:

- `docs/task/TASK-V2-003-bootstrap-db-interno.md`

Obiettivo della verifica:

- controllare se il task e stato seguito fedelmente
- controllare se il bootstrap DB interno e coerente con `DL-ARCH-V2-003`
- verificare che migration, seed e bootstrap locale siano eseguibili

## Sources Checked

- `docs/task/TASK-V2-003-bootstrap-db-interno.md`
- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
- `infra/docker/docker-compose.db.yml`
- `backend/src/nssp_v2/app/models/access.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260407_001_access_control_tables.py`
- `backend/scripts/seed_initial.py`
- `backend/src/nssp_v2/shared/config.py`
- `backend/tests/unit/test_models_access.py`

## Verification Summary

Esito complessivo: `Pass`

Motivo:

- i deliverable principali del task sono presenti e coerenti
- il bootstrap DB locale e verificabile con Docker Compose
- migration Alembic e seed iniziale risultano eseguibili nel setup dichiarato

Nota residua:

- il bootstrap backend resta sensibile a variabili ambiente locali incoerenti; durante la verifica e stato necessario forzare un ambiente pulito esplicito

## Fidelity Check

### Requisiti rispettati

- asset Docker locale presente in `infra/docker/docker-compose.db.yml`
- modelli SQLAlchemy presenti per `users`, `roles`, `user_roles`
- migration iniziale presente e coerente con i modelli
- seed minimo presente e idempotente
- configurazione backend estesa con `DATABASE_URL_TEST`
- guida di bootstrap/verifica aggiornata con i passaggi DB

### Osservazioni

- il task dichiarava 11 test unit al momento della chiusura
- oggi la suite unit backend e salita a 19 test per effetto di `TASK-V2-004`
- questo non e una deviazione del task, ma un avanzamento successivo compatibile

## Runtime Verification Performed

Comandi eseguiti:

- `docker compose -f infra/docker/docker-compose.db.yml up -d`
- `alembic upgrade head`
- `python scripts/seed_initial.py`
- `pytest tests/unit/ -v`

Risultati:

- Docker Compose: container PostgreSQL locale avviato correttamente
- Alembic: comando eseguito con successo su PostgreSQL attivo
- Seed: eseguito con successo, comportamento idempotente confermato
- Test unit backend: `19 passed`

Output significativo osservato:

- Alembic ha inizializzato correttamente il contesto PostgreSQL
- il seed ha rilevato ruoli, utente admin e mapping gia presenti senza creare duplicati

## Architecture Check

Allineamento con `DL-ARCH-V2-003`:

- DB interno PostgreSQL usato come backbone persistente: si
- primo slice persistente `users`, `roles`, `user_roles`: si
- migrazioni gestite via Alembic: si
- frontend non coinvolto direttamente nel DB: si

Non sono emerse violazioni architetturali evidenti nel perimetro del task.

## Risks And Notes

- il layer settings continua a essere fragile rispetto a `.env` locali non coerenti
- la verifica e stata riprodotta con env vars esplicite per isolare l'ambiente di test
- non e stato eseguito un test di integrazione dedicato con fixture DB separata

## Final Verdict

`TASK-V2-003` puo essere considerato verificato in modo sostanziale anche sul piano runtime.

Il prerequisito tecnico per auth browser e per la futura surface `admin` risulta disponibile.
