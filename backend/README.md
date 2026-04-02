# V2 Backend

Backend Python della V2.

Scopo:

- rendere espliciti i layer `sync`, `core`, `app`
- tenere separate infrastruttura tecnica e semantica di dominio
- permettere test e bootstrap indipendenti per layer

Layout:

- `src/nssp_v2/` package applicativo
- `alembic/` migrazioni schema
- `tests/` suite backend
