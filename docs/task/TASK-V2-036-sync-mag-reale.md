# TASK-V2-036 - Sync MAG_REALE

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il mirror sync read-only dei movimenti di magazzino da:

- `MAG_REALE`

verso il target interno:

- `sync_mag_reale`

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/integrations/easy/EASY_MAG_REALE.md`

## Goal

Costruire il primo mirror tecnico dei movimenti di magazzino come base del futuro calcolo canonico della giacenza articoli.

## Context

`MAG_REALE` e il primo caso V2 in cui il pattern corretto e:

- mirror `append-only`
- sync incrementale dei nuovi movimenti
- rebuild completo futuro a intervalli noti

Il task deve restare strettamente nel layer `sync` e non introdurre ancora il calcolo della giacenza.

## In Scope

- modello sync `sync_mag_reale`
- migration necessaria
- adapter Easy read-only per `MAG_REALE`
- bootstrap iniziale completo dei movimenti
- strategia incrementale sui nuovi movimenti
- normalizzazione tecnica di `ART_COD` per confronto cross-source:
  - trim
  - uppercase
  - rimozione spazi non significativi dove necessario
- script o command dedicato per esecuzione manuale
- run metadata e freshness anchor della sync unit

## Out of Scope

- calcolo `inventory_positions`
- UI magazzino
- scheduler automatico
- disponibilita / ATP
- multi-magazzino
- interpretazione business delle causali

## Constraints

- Easy solo `read-only`
- nessuna scrittura verso Easy in nessun caso
- il layer `sync` non deve calcolare giacenza
- l'allineamento deve essere coerente con:
  - `append_only`
  - `cursor` incrementale
  - `no_delete_handling`

## Acceptance Criteria

- esiste il target `sync_mag_reale`
- il bootstrap iniziale completo funziona
- la sync incrementale aggiunge solo nuovi movimenti
- `ART_COD` viene normalizzato tecnicamente come da mapping
- `ID_MAGREALE` viene trattato come identita tecnica del movimento
- run metadata e freshness vengono aggiornati correttamente
- `python -m pytest tests -q` passa

## Deliverables

- modelli sync `MAG_REALE`
- migration necessaria
- adapter Easy read-only
- sync unit dedicata
- script/command dedicato
- test backend minimi su:
  - mapping
  - idempotenza
  - incremental sync

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica della sync coerente col task.

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
- `src/nssp_v2/sync/mag_reale/__init__.py` — package vuoto
- `src/nssp_v2/sync/mag_reale/models.py` — `SyncMagReale` (tabella `sync_mag_reale`, PK id autoincrement, UNIQUE id_movimento, 5 campi dati + synced_at)
- `src/nssp_v2/sync/mag_reale/source.py` — `MagRealeRecord`, `MagRealeSourceAdapter` (ABC), `EasyMagRealeSource` (fetch_since con cursor), `FakeMagRealeSource`; `_normalize_codice_articolo` (strip + upper + None su vuoto)
- `src/nssp_v2/sync/mag_reale/unit.py` — `MagRealeSyncUnit` (ENTITY_CODE="mag_reale", append_only + cursor + no_delete_handling); applica `_normalize_codice_articolo` in scrittura
- `alembic/versions/20260408_012_sync_mag_reale.py` — crea `sync_mag_reale`
- `tests/sync/test_sync_mag_reale.py` — 16 test di integrazione

**Modificati:**
- `src/nssp_v2/app/services/sync_runner.py` — aggiunto `"mag_reale": MagRealeSyncUnit` in `_UNIT_MAP`
- `src/nssp_v2/app/api/sync.py` — aggiunti `POST /sync/surface/magazzino` e `GET /sync/freshness/magazzino`; import `EasyMagRealeSource`; costante `_MAGAZZINO_ENTITIES`

**Creati (post-task):**
- `scripts/sync_mag_reale.py` — script CLI on-demand; supporta `--source easy` (default, richiede `EASY_CONNECTION_STRING`) e `--source fake` (record demo); stampa run metadata a console; esce con codice 0 su successo, 1 su errore

### Migration introdotte

- `20260408_012_sync_mag_reale.py` — crea `sync_mag_reale` (down_revision: 20260407011)

### Script/command introdotti

- `POST /api/sync/surface/magazzino` — trigger via API (richiede backend avviato + token Bearer)
- `scripts/sync_mag_reale.py` — script CLI standalone:
  ```bash
  cd backend
  python scripts/sync_mag_reale.py              # da Easy (default)
  python scripts/sync_mag_reale.py --source fake # demo locale senza Easy
  ```

### Test eseguiti

16 test in `tests/sync/test_sync_mag_reale.py`:
- Mapping: inserisce record, mapping tutti i campi, campi nullable None ✓
- Normalizzazione: uppercase, trim, combinati, stringa vuota → None ✓
- Bootstrap: completo (cursor=0), idempotenza ✓
- Incrementale: aggiunge solo nuovi, cursor corretto, zero written se nulla di nuovo ✓
- No delete handling: record non presenti in sorgente restano nel mirror ✓
- Run metadata: log creato, freshness anchor aggiornato, log multipli ✓

Suite completa: 346/346 passed.

### Test non eseguiti

- Test HTTP degli endpoint `/surface/magazzino` e `/freshness/magazzino`: non inclusi; la logica è coperta dai test unitari della sync unit e il pattern degli endpoint è identico a quello delle altre surface già testate.
- Test con EasyMagRealeSource reale: non eseguibili senza connessione a Easy.

### Assunzioni

- Il cursor è `max(id_movimento)` nel mirror locale; ID_MAGREALE cresce monotonicamente in Easy (assunzione dichiarata in EASY_MAG_REALE.md).
- La normalizzazione `codice_articolo` (strip + upper) è applicata nella unit (non solo nell'Easy source) in modo che sia garantita anche con FakeSource e futuri adapter.
- In caso di esecuzione parziale fallita e rollback, il bootstrap successivo riesegue correttamente dall'ultimo id_movimento persistito.
- Nessun script standalone: il task specifica "script o command dedicato per esecuzione manuale" — si usa il trigger API esistente.

### Limiti noti

- La strategia `append_only` + `cursor` basata su `max(id_movimento)` dipende dall'assunzione che Easy non modifichi i record esistenti in MAG_REALE. Se questa assunzione viene violata, le modifiche non verranno catturate dal sync.
- Il rebuild completo (truncate + re-insert) non è ancora implementato: richiederà un endpoint o command dedicato quando verrà introdotto lo scheduler.
- La normalizzazione `codice_articolo` non rimuove gli spazi interni multipli: solo trim + upper. Estensione futura se necessario.
- Nessun endpoint di freshness/surface sul frontend (magazzino UI è fuori scope di questo task).

### Follow-up suggeriti

- Command o endpoint di rebuild completo (truncate + re-sync) per compensare derive nel tempo.
- Core slice `inventory_positions` (DL-ARCH-V2-016): aggregazione `sum(QTA_CAR) - sum(QTA_SCA)` per articolo.
- Scheduler periodico per bootstrap incrementale automatico.
- Validazione che il cursor non ritorni indietro dopo un rollback parziale.
