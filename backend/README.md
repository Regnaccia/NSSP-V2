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

---

## Bootstrap rapido

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -e ".[dev]"
pytest tests/unit/ -v
```

Guida completa: [`docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`](../docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md)
