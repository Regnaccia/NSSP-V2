# NSSP V2

Questo repository ospita codice, documentazione e artefatti runtime della V2.

Principi guida:

- `sync`, `core` e `app` devono essere visibili anche nella struttura del codice
- la V2 vive separata da `V0/` e `V1/`
- la documentazione generale V2 vive in `docs/`

Riferimenti architetturali primari:

- `docs/README.md`
- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`

## Struttura iniziale

```text
.
|-- docs/
|   |-- archive/
|   |-- charter/
|   |-- decisions/
|   |-- guides/
|   |-- roadmap/
|   `-- task/
|-- backend/
|   |-- alembic/
|   |   `-- versions/
|   |-- src/
|   |   `-- nssp_v2/
|   |       |-- app/
|   |       |-- core/
|   |       |-- shared/
|   |       `-- sync/
|   `-- tests/
|-- env/
|-- frontend/
|   `-- src/
|-- infra/
|   `-- docker/
`-- scripts/
```

## Regole operative

- `backend/src/nssp_v2/sync/` integra sorgenti esterne e scrive solo dati di sync o run metadata
- `backend/src/nssp_v2/core/` contiene fatti canonici, computed facts, aggregate, stati, policy e orchestrazione di rebuild
- `backend/src/nssp_v2/app/` espone API, workflow e projection senza reimplementare logica di dominio
- `backend/src/nssp_v2/shared/` ospita infrastruttura tecnica condivisa, non regole di business
- `frontend/` contiene solo UI e client applicativi; la logica di dominio resta nel backend
- `docs/` contiene la documentazione generale V2 divisa per tipo

## Test

I test backend sono separati per scopo:

- `tests/unit/` per logica core pura
- `tests/integration/` per API, DB e rebuild
- `tests/contracts/` per contratti tra layer
- `tests/sync/` per adapter, normalizzazione e integrazione sorgenti
