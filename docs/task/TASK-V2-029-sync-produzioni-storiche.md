# TASK-V2-029 - Sync produzioni storiche

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il mirror sync read-only delle produzioni storiche da:

- `SDPRE_PROD`

verso il target interno:

- `sync_produzioni_storiche`

## References

- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`

## Objective

Costruire il mirror tecnico delle produzioni storiche, separato da quello delle attive e coerente con il pattern V2 di mirror distinti per sorgente/bucket.

## Requirements

### Sync Unit

- introdurre la sync unit dedicata alle produzioni storiche
- leggere da `SDPRE_PROD` in modalita `read-only`
- allineare il target `sync_produzioni_storiche`

### Mapping

Applicare il mapping documentato in `EASY_PRODUZIONI.md`, gestendo correttamente le differenze tecniche note rispetto a `DPRE_PROD`.

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

- modelli sync `produzioni_storiche`
- migration necessaria
- adapter Easy read-only per `SDPRE_PROD`
- sync unit dedicata
- script o command dedicato
- test backend minimi su mapping e idempotenza

## Out of Scope

- produzioni attive
- Core `produzioni`
- bucket `active | historical`
- `stato_produzione`
- `forza_completata`
- UI `produzioni`

## Verification

La verifica minima deve dimostrare:

- lettura read-only da `SDPRE_PROD`
- popolamento corretto di `sync_produzioni_storiche`
- idempotenza della sync
- aggiornamento di run metadata e freshness

## Expected Commands

- bootstrap backend come da `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
- comando dedicato di sync per `produzioni_storiche`
- test backend mirati

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- script/command introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/sync/produzioni_storiche/__init__.py`
- `src/nssp_v2/sync/produzioni_storiche/models.py` — `SyncProduzioneStorica`, tabella `sync_produzioni_storiche`
- `src/nssp_v2/sync/produzioni_storiche/source.py` — `ProduzioneStoricaRecord`, `EasyProduzioneStoricaSource` (SELECT da SDPRE_PROD), `FakeProduzioneStoricaSource`
- `src/nssp_v2/sync/produzioni_storiche/unit.py` — `ProduzioneStoricaSyncUnit` (ENTITY_CODE="produzioni_storiche")
- `alembic/versions/20260407_010_sync_produzioni_storiche.py`
- `scripts/sync_produzioni_storiche.py`
- `tests/sync/test_sync_produzioni_storiche.py`

**Modificati:**
- `src/nssp_v2/app/services/sync_runner.py` — aggiunta `"produzioni_storiche": ProduzioneStoricaSyncUnit` a `_UNIT_MAP`
- `src/nssp_v2/app/services/admin_policy.py` — fix `HTTP_422_UNPROCESSABLE_CONTENT` → `422` (starlette version compat)

### Migration introdotte

- `20260407_010_sync_produzioni_storiche.py` — crea tabella `sync_produzioni_storiche`; applicata con `alembic upgrade head`

### Script/command introdotti

- `scripts/sync_produzioni_storiche.py --source easy|fake`

### Test eseguiti

11 test di integrazione in `tests/sync/test_sync_produzioni_storiche.py`:
- `test_inserisce_record` ✓
- `test_mapping_tutti_i_campi` ✓
- `test_campi_nullable_none` ✓
- `test_upsert_idempotente` ✓
- `test_upsert_aggiorna_campo` ✓
- `test_upsert_piu_record` ✓
- `test_mark_inactive_record_rimosso` ✓
- `test_riattiva_record_reinserito` ✓
- `test_run_log_creato` ✓
- `test_freshness_anchor_aggiornato` ✓
- `test_run_log_multipli` ✓

Suite completa: 289/289 passed.

### Test non eseguiti

- Test con sorgente Easy reale (pyodbc/SDPRE_PROD): ambiente di sviluppo non ha accesso al DB EasyJob.

### Assunzioni

- `ID_DETTAGLIO` è source identity key unica e non-null in SDPRE_PROD (confermato da EASY_PRODUZIONI.md).
- Struttura campi SDPRE_PROD identica a DPRE_PROD ad eccezione del campo `scritto` (lowercase, non mappato).
- Delete handling `mark_inactive`: record non più in sorgente restano nella tabella con `attivo=False`.

### Limiti noti

- `COD_RIGA` e `scritto` non mappati (deferred come da EASY_PRODUZIONI.md §Structural Check).
- Full scan a ogni run: non c'è change detection incrementale (coerente con `full_scan` per questa entità).

### Follow-up suggeriti

- TASK-V2-030: Core produzioni — bucket active/historical + stato aggregato (entità successiva nella pipeline).
