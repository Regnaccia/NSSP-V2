# TASK-V2-044 - Customer set aside

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`

## Goal

Costruire il primo computed fact canonico `customer_set_aside`, derivato da `DOC_QTAP`, come quota gia
appartata per cliente ma ancora distinta sia da `inventory` sia da `commitments`.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`

## Context

Con `DL-ARCH-V2-019` la V2 ha introdotto un nuovo fact intermedio:

- `customer_set_aside`

Questo fact rappresenta la quota:

- gia inscatolata o appartata per il cliente
- non ancora evasa
- ancora presente nello stock fisico
- ma non piu giacenza libera

Nel perimetro V1 la sorgente corretta non e il mirror sync grezzo, ma il Core:

- `customer_order_lines`

Il task deve quindi trasformare `set_aside_qty` del Core ordini in una fact separata, riusabile dalla
futura `availability`.

## Scope

### In Scope

- modello Core `customer_set_aside` o equivalente
- provenienza iniziale `source_type = customer_order`
- calcolo della quantita appartata da `customer_order_lines.set_aside_qty`
- campi canonici minimi:
  - `article_code`
  - `source_type`
  - `source_reference`
  - `set_aside_qty`
  - `computed_at`
- query/read model aggregato almeno per `article_code`
- esclusione delle righe con `set_aside_qty <= 0`

### Out of Scope

- `availability`
- allocazioni
- impegni produzione
- UI dedicata
- logiche di spedizione o picking
- deduzioni avanzate oltre la quantita gia appartata

## Constraints

- il task deve leggere dal Core ordini, non dal mirror `sync_righe_ordine_cliente`
- `customer_set_aside` deve restare separato da `commitments`
- `customer_set_aside` deve restare separato da `inventory_positions`
- le righe con `set_aside_qty <= 0` non devono generare fact attivi
- `source_reference` deve permettere di risalire alla riga ordine canonica

## Acceptance Criteria

- esiste un computed fact `customer_set_aside` o equivalente per `source_type = customer_order`
- `set_aside_qty` viene calcolata usando `customer_order_lines.set_aside_qty`
- le righe con `set_aside_qty <= 0` non generano record attivi
- esiste almeno una query/read model aggregata per `article_code`
- `python -m pytest tests -q` passa

## Deliverables

- modelli Core `customer_set_aside`
- eventuale migration necessaria
- query/read models minimi
- test backend minimi su:
  - mapping da `customer_order_lines`
  - esclusione righe senza quota appartata
  - aggregazione per articolo
  - tracciabilita tramite `source_reference`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del computed fact `customer_set_aside`.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- computed fact/read models introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- mantenere il perimetro V1 stretto: solo `customer_order`
- non introdurre ancora `availability`
- non comprimere `customer_set_aside` dentro `commitments`
- lasciare `source_reference` abbastanza ricco da risalire alla riga ordine canonica

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/core/customer_set_aside/__init__.py` — package; esporta `rebuild_customer_set_aside`, `list_customer_set_aside`, `get_customer_set_aside_by_article`, `CustomerSetAsideItem`, `CustomerSetAsideByArticleItem`
- `src/nssp_v2/core/customer_set_aside/models.py` — `CoreCustomerSetAside` (tabella `core_customer_set_aside`, 5 campi + indici su `article_code` e `source_type`)
- `src/nssp_v2/core/customer_set_aside/read_models.py` — `CustomerSetAsideItem` (per riga), `CustomerSetAsideByArticleItem` (aggregato per articolo); entrambi frozen Pydantic
- `src/nssp_v2/core/customer_set_aside/queries.py` — `rebuild_customer_set_aside`, `list_customer_set_aside`, `get_customer_set_aside_by_article`
- `alembic/versions/20260409_016_core_customer_set_aside.py` — migration
- `tests/core/test_core_customer_set_aside.py` — 18 test di integrazione

### Migration introdotte

- `20260409_016_core_customer_set_aside.py` — crea `core_customer_set_aside` con indici su `article_code` e `source_type` (down_revision: 20260409015)

### Computed fact / read models introdotti

- `rebuild_customer_set_aside(session) -> int` — rebuild completo: DELETE + lettura Core ordini + INSERT; filtra `set_aside_qty > 0` e `article_code is not None`; restituisce n. righe create; il chiamante gestisce commit
- `list_customer_set_aside(session, source_type=None) -> list[CustomerSetAsideItem]` — tutti i record attivi, opzionalmente filtrati per `source_type`
- `get_customer_set_aside_by_article(session, article_code=None) -> list[CustomerSetAsideByArticleItem]` — aggregazione per `article_code` (sum `set_aside_qty`, count righe)

**Struttura `CustomerSetAsideItem`:**
```
article_code, source_type, source_reference, set_aside_qty, computed_at
```

**Struttura `CustomerSetAsideByArticleItem`:**
```
article_code, total_set_aside_qty, set_aside_count, computed_at
```

**source_reference** per `customer_order`: `"{order_reference}/{line_reference}"` — permette di risalire alla riga canonica senza FK persistita.

### Sequenza rebuild

```
rebuild_customer_set_aside(session)
  ├─ list_customer_order_lines(session)    — legge Core ordini (da sync_righe_ordine_cliente)
  ├─ filtra set_aside_qty > 0 e article_code not None
  ├─ DELETE all core_customer_set_aside
  └─ INSERT CoreCustomerSetAside per ogni riga appartata attiva (set_aside_qty = DOC_QTAP)
```

### Test eseguiti

18 test in `tests/core/test_core_customer_set_aside.py`:
- set_aside_qty = DOC_QTAP (valore dalla riga canonica) ✓
- source_type = "customer_order" ✓
- source_reference formato "{order_ref}/{line_ref}" ✓
- set_aside_qty = None → nessun record ✓
- set_aside_qty = 0 → nessun record ✓
- set_aside_qty < 0 → nessun record ✓
- article_code = None → nessun record ✓
- set_aside_qty > 0 → record creato ✓
- aggregazione piu righe stesso articolo ✓
- aggregazione articoli diversi separati ✓
- get_customer_set_aside_by_article singolo articolo ✓
- get_customer_set_aside_by_article articolo inesistente → [] ✓
- list_customer_set_aside con filtro source_type ✓
- rebuild deterministico ✓
- rebuild ricalcola dopo aggiornamento mirror ✓
- rebuild rimuove record di righe azzerate ✓
- mirror vuoto → 0 record ✓
- separazione da commitments: set_aside_qty != open_qty sullo stesso articolo ✓

Suite completa: 453/453 passed.

### Test non eseguiti

- Test HTTP su eventuali endpoint API: non inclusi — il task non introduce API.
- Test con dati reali Easy: non eseguibili senza connessione.

### Assunzioni

- `set_aside_qty = DOC_QTAP` (V1): la quantita appartata viene letta direttamente da `customer_order_lines.set_aside_qty`, senza ulteriori deduzioni.
- Il rebuild legge dal Core ordini (`list_customer_order_lines`), non direttamente da `sync_righe_ordine_cliente`.
- `source_reference` e una stringa leggibile (non una FK): permette tracciabilita senza accoppiamento strutturale.
- Il rebuild e delete-all + re-insert (non upsert): deterministico, stesso input stesso output.
- Il chiamante gestisce il commit (come `rebuild_commitments` e `rebuild_inventory_positions`).
- I valori `None` di `set_aside_qty` non generano record: semanticamente equivalenti a 0.

### Limiti noti

- V1 solo `customer_order`: provenienza unica, architettura pronta per future sorgenti tramite `source_type`.
- Nessun endpoint API esposto: il contratto e consumabile da moduli futuri via import Python.
- Nessun scheduler automatico del rebuild.
- Il rebuild ha costo O(n) sulle righe ordine attive.

### Follow-up suggeriti

- Computed fact `availability = inventory - commitments - set_aside` (DL-ARCH-V2-019 §8).
- Endpoint `POST /api/core/customer-set-aside/rebuild` per trigger manuale.
- Integrazione del rebuild nel flusso `trigger_produzione` (dopo sync righe ordine).
- Surface UI con visualizzazione quota appartata per articolo.

## Completed At

2026-04-09

## Completed By

Claude Code
