# TASK-V2-028 - Sync produzioni attive

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il mirror sync read-only delle produzioni attive da:

- `DPRE_PROD`

verso il target interno:

- `sync_produzioni_attive`

## References

- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`

## Objective

Costruire il primo mirror tecnico delle produzioni attive, mantenendo il confine `sync` strettamente read-only e senza introdurre ancora logica Core o UI.

## Requirements

### Sync Unit

- introdurre la sync unit dedicata alle produzioni attive
- leggere da `DPRE_PROD` in modalita `read-only`
- allineare il target `sync_produzioni_attive`

### Mapping

Applicare il mapping documentato in `EASY_PRODUZIONI.md` per i campi rilevanti del primo slice.

### Contratto Sync

- source identity candidata: `ID_DETTAGLIO`
- alignment strategy: `upsert`
- change acquisition strategy: `full_scan`
- nessun computed fact nel layer `sync`
- nessun bucket applicativo nel layer `sync`

### Runtime

- aggiornare run metadata e freshness anchor della sync unit
- introdurre script o comando dedicato per esecuzione manuale

## Deliverables

- modelli sync `produzioni_attive`
- migration necessaria
- adapter Easy read-only per `DPRE_PROD`
- sync unit dedicata
- script o command dedicato
- test backend minimi su mapping e idempotenza

## Out of Scope

- produzioni storiche
- Core `produzioni`
- bucket `active | historical`
- `stato_produzione`
- `forza_completata`
- UI `produzioni`

## Verification

La verifica minima deve dimostrare:

- lettura read-only da `DPRE_PROD`
- popolamento corretto di `sync_produzioni_attive`
- idempotenza della sync
- aggiornamento di run metadata e freshness

## Expected Commands

- bootstrap backend come da `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
- comando dedicato di sync per `produzioni_attive`
- test backend mirati

## Completion Output

### File creati

- `src/nssp_v2/sync/produzioni_attive/__init__.py`
- `src/nssp_v2/sync/produzioni_attive/models.py` — `SyncProduzioneAttiva` (16 campi mappati + `attivo` + `synced_at`)
- `src/nssp_v2/sync/produzioni_attive/source.py` — `ProduzioneAttivaRecord`, `ProduzioneAttivaSourceAdapter`, `EasyProduzioneAttivaSource`, `FakeProduzioneAttivaSource`
- `src/nssp_v2/sync/produzioni_attive/unit.py` — `ProduzioneAttivaSyncUnit` (contratto DL-ARCH-V2-009 completo)
- `alembic/versions/20260407_009_sync_produzioni_attive.py` — tabella `sync_produzioni_attive`
- `scripts/sync_produzioni_attive.py` — `--source easy|fake`
- `tests/sync/test_sync_produzioni_attive.py` — 11 test

### File modificati

- `src/nssp_v2/app/services/sync_runner.py` — aggiunto `"produzioni_attive": ProduzioneAttivaSyncUnit`

### Migration

- `20260407009` — `CREATE TABLE sync_produzioni_attive` applicata via `alembic upgrade head`

### Test eseguiti

- `tests/sync/test_sync_produzioni_attive.py` — 11 passed
- `tests` (full suite) — 278 passed

### Test non eseguiti

- Nessuno. La sync con Easy reale richiede connessione al server SQL che non è accessibile in CI.

### Assunzioni

- `ID_DETTAGLIO` è confermato come source identity key: non ha FK dichiarata nel catalogo ma è `nullable=False` e sufficientemente discriminante.
- Delete handling `mark_inactive`: le produzioni che escono da `DPRE_PROD` vengono marcate inattive (non cancellate); il Core deciderà cosa farne in base al bucket.
- `riferimento_riga_ordine_cliente` (numeric 18,0) mappato come `Decimal` per evitare overflow su Integer.

### Limiti noti

- `full_scan` su `DPRE_PROD`: per dataset grandi potrebbe essere lento; watermark futuro opzionale.
- I campi `deferred` in EASY_PRODUZIONI.md non sono inclusi (out of scope per questo task).

### Follow-up suggeriti

- TASK-V2-029: sync `produzioni_storiche` da `SDPRE_PROD` (struttura quasi identica).
- TASK-V2-030: Core produzioni — bucket `active/historical` + stato aggregato.
