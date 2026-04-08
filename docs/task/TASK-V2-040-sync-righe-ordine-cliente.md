# TASK-V2-040 - Sync righe ordine cliente

## Status
Completed

## Date
2026-04-08

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`

## Goal

Implementare il primo mirror sync read-only delle righe ordine cliente da `V_TORDCLI` verso il target interno:

- `sync_righe_ordine_cliente`

come base tecnica per il futuro Core `ordini` e per i futuri `commitments` cliente.

## Context

Easy non espone una vera tabella ordini separata, ma una vista di righe ordine:

- `V_TORDCLI`

La granularita reale di partenza e quindi:

- `customer_order_line`

Il task deve restare strettamente nel layer `sync` e preservare:

- i riferimenti ordine/riga
- i dati cliente/articolo/quantita
- le righe descrittive di continuazione con `COLL_RIGA_PREC = true`
- il dato `DOC_QTAP` come stato intermedio sorgente distinto

## Scope

### In Scope

- modello sync `sync_righe_ordine_cliente`
- migration necessaria
- adapter Easy read-only per `V_TORDCLI`
- strategia iniziale `upsert` con `full_scan`
- source identity proposta `(DOC_NUM, NUM_PROGR)`
- preservazione delle righe descrittive con `COLL_RIGA_PREC = true`
- salvataggio di `DOC_QTAP` come dato sorgente distinto (`set_aside_qty`)
- script o command dedicato per esecuzione manuale
- run metadata e freshness anchor della sync unit

### Out of Scope

- Core `ordini`
- aggregazione `description_lines`
- calcolo `open_qty`
- calcolo `commitments` cliente
- UI ordini
- disponibilita
- scheduler automatico

## Constraints

- Easy solo `read-only`
- nessuna scrittura verso Easy in nessun caso
- il layer `sync` non deve aggregare righe descrittive
- il layer `sync` non deve interpretare `DOC_QTAP` come `availability`
- il mirror deve preservare la forma sorgente quanto piu possibile

## Acceptance Criteria

- esiste il target `sync_righe_ordine_cliente`
- la sync legge `V_TORDCLI` e persiste almeno i campi V1 documentati
- la source identity `(DOC_NUM, NUM_PROGR)` viene usata in modo coerente nel mirror
- le righe con `COLL_RIGA_PREC = true` vengono salvate come righe distinte
- `DOC_QTAP` viene salvato come dato sorgente distinto, senza business logic aggiuntiva
- run metadata e freshness vengono aggiornati correttamente
- `python -m pytest tests -q` passa

## Deliverables

- modelli sync `righe_ordine_cliente`
- migration necessaria
- adapter Easy read-only `V_TORDCLI`
- sync unit dedicata
- script/command dedicato
- test backend minimi su:
  - mapping
  - identity `(DOC_NUM, NUM_PROGR)`
  - righe `COLL_RIGA_PREC`
  - idempotenza base

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

## Implementation Notes

Direzione raccomandata:

- mantenere `full_scan` nel primo slice, evitando ottimizzazioni premature
- preservare le righe descrittive senza fonderle nel `sync`
- trattare `DOC_QTAP` come dato sorgente strutturale utile ai futuri stream `commitments` / `availability`
- non introdurre ancora la testata ordine come entita sync separata

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/sync/righe_ordine_cliente/__init__.py` — package vuoto
- `src/nssp_v2/sync/righe_ordine_cliente/models.py` — `SyncRigaOrdineCliente` (tabella `sync_righe_ordine_cliente`, PK id autoincrement, UNIQUE `(order_reference, line_reference)`, 17 campi + synced_at)
- `src/nssp_v2/sync/righe_ordine_cliente/source.py` — `RigaOrdineClienteRecord`, `RigaOrdineClienteSourceAdapter` (ABC), `EasyRigheOrdineClienteSource` (fetch_all da V_TORDCLI), `FakeRigheOrdineClienteSource`; `_strip_or_none`, `_to_bool`
- `src/nssp_v2/sync/righe_ordine_cliente/unit.py` — `RigheOrdineClienteSyncUnit` (ENTITY_CODE="righe_ordine_cliente", upsert + full_scan + no_delete_handling)
- `alembic/versions/20260408_014_sync_righe_ordine_cliente.py` — migration
- `tests/sync/test_sync_righe_ordine_cliente.py` — 16 test di integrazione
- `scripts/sync_righe_ordine_cliente.py` — script CLI standalone

**Modificati:**
- `src/nssp_v2/app/services/sync_runner.py` — aggiunto `"righe_ordine_cliente": RigheOrdineClienteSyncUnit` in `_UNIT_MAP`

### Migration introdotte

- `20260408_014_sync_righe_ordine_cliente.py` — crea `sync_righe_ordine_cliente` (down_revision: 20260408013)

### Script/command introdotti

- `scripts/sync_righe_ordine_cliente.py` — script CLI standalone:
  ```bash
  cd backend
  python scripts/sync_righe_ordine_cliente.py              # da Easy (default)
  python scripts/sync_righe_ordine_cliente.py --source fake # demo locale senza Easy
  ```

### Field mapping implementato

| Source (V_TORDCLI) | Target (sync_righe_ordine_cliente) | Tipo sorgente |
|--------------------|-------------------------------------|---------------|
| `DOC_NUM` | `order_reference` | varchar(10) |
| `NUM_PROGR` | `line_reference` | numeric(4,0) → int |
| `DOC_DATA` | `order_date` | datetime |
| `DOC_PREV` | `expected_delivery_date` | datetime |
| `CLI_COD` | `customer_code` | varchar(6) |
| `PDES_COD` | `destination_code` | varchar(6) |
| `NUM_PROGR_CLIENTE` | `customer_destination_progressive` | varchar(6) |
| `N_ORDCLI` | `customer_order_reference` | varchar(20) |
| `ART_COD` | `article_code` | varchar(25), nullable |
| `ART_DESCR` | `article_description_segment` | varchar(100) |
| `ART_MISURA` | `article_measure` | varchar(20) |
| `DOC_QTOR` | `ordered_qty` | numeric(13,5) |
| `DOC_QTEV` | `fulfilled_qty` | numeric(13,5) |
| `DOC_QTAP` | `set_aside_qty` | numeric(18,5) |
| `DOC_PZ_NETTO` | `net_unit_price` | numeric(18,5) |
| `COLL_RIGA_PREC` | `continues_previous_line` | bit → bool |

### Test eseguiti

16 test in `tests/sync/test_sync_righe_ordine_cliente.py`:
- Mapping: inserisce record, tutti i campi, campi nullable None ✓
- Source identity: righe stessa ordine, ordini diversi ✓
- Righe descrittive: continues_previous_line=True salvata come record separato ✓
- Righe descrittive multiple non fuse nel mirror ✓
- Upsert: aggiorna riga esistente, non duplica, aggiorna set_aside_qty ✓
- Idempotenza: stessa sorgente stesso risultato ✓
- No delete handling: riga sparita resta nel mirror ✓
- set_aside_qty preservato senza business logic ✓
- Run metadata: log creato, freshness aggiornato ✓
- Sorgente vuota: 0 righe, run di successo ✓

Suite completa: 377/377 passed.

### Test non eseguiti

- Test HTTP degli endpoint (non ne sono stati aggiunti): la sync unit e accessibile tramite SyncRunner; endpoint dedicato e un follow-up.
- Test con EasyRigheOrdineClienteSource reale: non eseguibili senza connessione a Easy.

### Assunzioni

- `(DOC_NUM, NUM_PROGR)` e assunta stabile come source identity (non dichiarata come PK in V_TORDCLI, assunzione da EASY_RIGHE_ORDINE_CLIENTE.md).
- Righe con `DOC_NUM` o `NUM_PROGR` NULL vengono scartate da `EasyRigheOrdineClienteSource`: non possono essere identificate come source identity.
- `NUM_PROGR` e numeric(4,0) in SQL Server — viene castato a `int` prima del mapping.
- `COLL_RIGA_PREC` e un campo `bit` — convertito a `bool | None` tramite `_to_bool`.
- Il layer sync non interpreta `set_aside_qty` (DOC_QTAP): viene salvato identico alla sorgente.
- Il layer sync non fonde righe descrittive: ogni riga resta un record distinto.
- `no_delete_handling`: le righe non piu in V_TORDCLI restano nel mirror; la politica sara rivalutata quando sara chiaro il ciclo di vita degli ordini chiusi.

### Limiti noti

- La conferma che `(DOC_NUM, NUM_PROGR)` sia sempre stabile e univoca e aperta (vedi open questions in EASY_RIGHE_ORDINE_CLIENTE.md).
- `full_scan` legge tutta la vista a ogni esecuzione: per dataset grandi puo essere lento; cursor incrementale e un follow-up naturale.
- Non e ancora chiaro se V_TORDCLI contenga solo righe aperte o anche storico chiuso.
- Nessun endpoint API dedicato per questa sync surface: la unit e registrata in `_UNIT_MAP` ma non esposta ancora tramite router.

### Follow-up suggeriti

- Endpoint `POST /api/sync/surface/ordini` (o estensione di una surface esistente) per trigger on demand.
- Core `ordini` / `righe_ordine`: read model canonico con calcolo `open_qty` e stato apertura.
- Computed fact `commitments` da righe ordine aperte (DL-ARCH-V2-017).
- Cursor incrementale basato su data o identificatore di modifica ordine, se disponibile in Easy.
- Chiarire il ruolo di `set_aside_qty` nella futura formula di disponibilita.
