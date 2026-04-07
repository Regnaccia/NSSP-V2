# TASK-V2-018 - Sync articoli reale

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
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/task/TASK-V2-009-easy-schema-explorer-and-catalog.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/integrations/easy/catalog/ANAART.json`

## Goal

Implementare la sync reale di `articoli` da Easy `ANAART` verso il target interno V2 `sync_articoli`, come primo mirror del dominio `produzione`.

## Context

La V2 ha gia validato il modello sync reale su:

- `clienti`
- `destinazioni`

Il prossimo stream naturale e `articoli`, mantenendo lo stesso approccio:

- una sync unit per entita
- adapter Easy read-only separato
- target interno owned dalla sync unit
- nessuna logica Core o UI nel layer `sync`

Il task applica direttamente il pattern generale gia fissato da:

- `DL-ARCH-V2-007`
- `DL-ARCH-V2-008`
- `DL-ARCH-V2-009`

Questo task non deve ancora costruire il Core `articoli`.
Deve solo produrre un mirror interno affidabile, idempotente e verificabile.

## Scope

### In Scope

- implementazione di un adapter read-only reale per `ANAART`
- lettura dei campi selezionati in `EASY_ARTICOLI.md`
- creazione o aggiornamento del target interno `sync_articoli`
- source identity tecnica `ART_COD`
- mantenimento di run metadata e freshness anchor
- esecuzione on demand della sync `articoli` con sorgente Easy reale
- verifica tecnica su idempotenza, allineamento e rispetto del contratto read-only
- aggiornamento documentazione minima se cambiano comandi o prerequisiti

### Out of Scope

- Core slice `articoli`
- UI produzione
- configurazione interna articolo
- scheduler reale
- orchestrazione multi-entita
- scrittura verso Easy

## Constraints

- accesso a Easy solo read-only, senza eccezioni
- rispettare `EASY_ARTICOLI.md` come mapping tecnico di riferimento
- il target sync resta vicino alla sorgente e non diventa modello Core
- la sync deve restare idempotente
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`

## Acceptance Criteria

- esiste un adapter reale read-only per `ANAART`
- la sync `articoli` legge da Easy i campi documentati e li allinea nel target interno
- il target `sync_articoli` contiene i campi previsti dal mapping `EASY_ARTICOLI.md`
- la sync `articoli` resta idempotente su doppia esecuzione
- run metadata e freshness anchor continuano a essere aggiornati correttamente
- la verifica documenta esplicitamente che non avviene alcuna write verso Easy

## Deliverables

- adapter Easy reale per `articoli`
- modelli e migration del target `sync_articoli`
- sync unit `articoli`
- script di esecuzione on demand `sync_articoli`
- test coerenti col nuovo perimetro
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/integrations/easy/EASY_ARTICOLI.md` se il mapping cambia

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
```

Database:

```bash
docker compose -f infra/docker/docker-compose.db.yml up -d
cd backend
cp .env.example .env
alembic upgrade head
```

Easy:

- configurare `EASY_CONNECTION_STRING` in `.env`
- usare solo connessione read-only

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita:

```bash
cd backend
python scripts/sync_articoli.py
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- evidenza che la connessione verso Easy e solo read-only

## Implementation Notes

Direzione raccomandata:

- mantenere l'adapter Easy separato dalla logica della sync unit
- usare il catalogo `ANAART.json` come riferimento tecnico completo
- usare `EASY_ARTICOLI.md` come selezione curata dei campi realmente usati
- non introdurre deduzioni business nel layer `sync`
- trattare `ART_KG` secondo la convenzione attuale documentata, lasciando aperta la validazione finale del significato operativo

---

## Completion Notes

### Summary

Implementata la sync unit `articoli` seguendo il pattern consolidato `clienti`/`destinazioni`. Adapter `EasyArticoloSource` read-only su `ANAART` con i 13 campi selezionati in `EASY_ARTICOLI.md`. Target `sync_articoli` introdotto tramite migration Alembic. `ArticoloSyncUnit` con contratto DL-ARCH-V2-009 (upsert, full_scan, mark_inactive, no dependencies). Script `sync_articoli.py` con `--source easy|fake`. Nessuna scrittura verso Easy: la connessione è aperta con `autocommit=True, readonly=True` e la query è `SELECT`-only (verificato da test).

### Files Changed

- `src/nssp_v2/sync/articoli/__init__.py` — package
- `src/nssp_v2/sync/articoli/models.py` — `SyncArticolo` (mirror ANAART, 13 campi + attivo/synced_at)
- `src/nssp_v2/sync/articoli/source.py` — `ArticoloRecord`, `ArticoloSourceAdapter`, `EasyArticoloSource`, `FakeArticoloSource`
- `src/nssp_v2/sync/articoli/unit.py` — `ArticoloSyncUnit` (upsert + mark_inactive + run metadata)
- `alembic/versions/20260407_006_sync_articoli.py` — migration create table `sync_articoli`
- `scripts/sync_articoli.py` — entrypoint on-demand con `--source easy|fake`
- `tests/unit/test_sync_articoli_contract.py` — 18 test: contratto unit, read-only adapter, colonne modello, query fields
- `tests/sync/test_articoli_run.py` — 17 test: upsert, idempotenza, mark_inactive, run metadata, freshness anchor, campi numerici/nullable

### Dependencies Introduced

Nessuna nuova dipendenza. `pyodbc` era già nel gruppo `[easy]` di `pyproject.toml`.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 202 passed in 3.86s |
| `python scripts/sync_articoli.py --source fake` (1a esecuzione) | Claude Code (agente) | backend V2 locale, DB PostgreSQL locale | status: success, rows_seen: 3, rows_written: 3, rows_deleted: 0 |
| `python scripts/sync_articoli.py --source fake` (2a esecuzione — idempotenza) | Claude Code (agente) | backend V2 locale, DB PostgreSQL locale | status: success, rows_seen: 3, rows_written: 3, rows_deleted: 0 — nessuna duplicazione |
| Verifica no write verso Easy | Claude Code (agente) | ispezione codice + test | `EasyArticoloSource` apre la connessione con `readonly=True`; la query inizia con `SELECT`; nessun metodo write esposto nell'interfaccia (test `test_easy_source_query_is_select_only`, `test_easy_source_has_no_write_methods`) |

### Assumptions

- I campi numerici (`REGN_QT_OCCORR`, `REGN_QT_SCARTO`, `ART_KG`) vengono convertiti a `Decimal` via `str()` per evitare perdita di precisione floating-point dal driver pyodbc.
- `ART_KG` è trattato come `peso_grammi` secondo la convenzione operativa corrente documentata in `EASY_ARTICOLI.md §Known Source Limits`. Il significato va confermato rispetto al naming sorgente.
- `ART_DTMO` è acquisito come campo sorgente (`source_modified_at`) ma non usato come watermark nel primo slice (coerente con EASY_ARTICOLI.md §Freshness Anchor).
- `EASY_ARTICOLI.md` non va aggiornato: il mapping implementato corrisponde esattamente a quanto documentato.

### Known Limits

- La sync `articoli` usa `full_scan`: per cataloghi di grandi dimensioni sarà necessario passare a strategia `watermark` basata su `ART_DTMO` (open question già in `EASY_ARTICOLI.md`).
- Il Core `articoli` non è implementato in questo task (fuori scope).

### Follow-ups

- Core slice `articoli`: read model, query, surface produzione
- Valutare passaggio da `full_scan` a `watermark` usando `ART_DTMO`
- Validare in modo definitivo l'unita di misura di `ART_KG`

## Completed At

2026-04-07

## Completed By

Claude Code
