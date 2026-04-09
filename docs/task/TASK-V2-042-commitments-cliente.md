# TASK-V2-042 - Commitments cliente

## Status
Completed

## Date
2026-04-08

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`

## Goal

Costruire il primo computed fact `commitments` da provenienza `customer_order`, a partire dal Core
`customer_order_lines`, come base riusabile per i futuri calcoli di `availability`.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`

## Context

Con `DL-ARCH-V2-017` la V2 ha introdotto `commitments` come computed fact canonico del Core.

Per la provenienza `customer_order`, il building block corretto non e il mirror sync grezzo ma:

- `customer_order_lines`

Il primo slice V1 dei commitments cliente deve quindi:

- leggere le righe ordine canoniche dal Core
- produrre una fact uniforme `commitments`
- usare come quantita impegnata la quota ancora davvero da coprire operativamente

Nel perimetro V1:

- `committed_qty = open_qty`

dove `open_qty` arriva gia dal Core ordini e tiene conto di:

- ordinato
- evaso
- quantita gia inscatolata/appartata

## Scope

### In Scope

- modello Core `commitments` o equivalente
- provenienza iniziale `source_type = customer_order`
- calcolo `committed_qty` da `customer_order_lines.open_qty`
- campi canonici minimi:
  - `article_code`
  - `source_type`
  - `source_reference`
  - `committed_qty`
  - `computed_at`
- read model/query di aggregazione almeno per `article_code`
- esclusione delle righe con `open_qty <= 0`

### Out of Scope

- commitments da `production`
- disponibilita finale
- allocazioni
- priorita
- compensazioni tra sorgenti
- UI dedicata commitments

## Constraints

- il task deve leggere dal Core ordini, non dal mirror `sync_righe_ordine_cliente`
- `committed_qty` cliente V1 deve coincidere con `open_qty`
- gli stati `set_aside_qty` e `fulfilled_qty` restano visibili a monte nel Core ordini, ma non devono generare doppio conteggio
- il modello deve restare compatibile con future provenienze aggiuntive

## Acceptance Criteria

- esiste un computed fact `commitments` per `source_type = customer_order`
- `committed_qty` viene calcolata usando `open_qty`
- le righe con `open_qty <= 0` non generano commitments attivi
- esiste almeno una query/read model aggregata per `article_code`
- `python -m pytest tests -q` passa

## Deliverables

- modelli Core `commitments`
- eventuale migration necessaria
- query/read models minimi
- test backend minimi su:
  - mapping da `customer_order_lines`
  - esclusione righe chiuse
  - aggregazione per articolo
  - `committed_qty = open_qty`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del computed fact `commitments`.

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
- non anticipare deduzioni avanzate oltre `committed_qty = open_qty`
- lasciare `source_reference` abbastanza ricco da risalire alla riga ordine canonica

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/core/commitments/__init__.py` — package; esporta `rebuild_commitments`, `list_commitments`, `get_commitments_by_article`, `CommitmentItem`, `CommitmentsByArticleItem`
- `src/nssp_v2/core/commitments/models.py` — `CoreCommitment` (tabella `core_commitments`, 5 campi + indici su `article_code` e `source_type`)
- `src/nssp_v2/core/commitments/read_models.py` — `CommitmentItem` (per riga), `CommitmentsByArticleItem` (aggregato per articolo); entrambi frozen Pydantic
- `src/nssp_v2/core/commitments/queries.py` — `rebuild_commitments`, `list_commitments`, `get_commitments_by_article`
- `alembic/versions/20260409_015_core_commitments.py` — migration
- `tests/core/test_core_commitments.py` — 16 test di integrazione

### Migration introdotte

- `20260409_015_core_commitments.py` — crea `core_commitments` con indici su `article_code` e `source_type` (down_revision: 20260408014)

### Computed fact / read models introdotti

- `rebuild_commitments(session) -> int` — rebuild completo: DELETE + lettura Core ordini + INSERT; filtra `open_qty > 0` e `article_code is not None`; restituisce n. righe create; il chiamante gestisce commit
- `list_commitments(session, source_type=None) -> list[CommitmentItem]` — tutti i commitments attivi, opzionalmente filtrati per `source_type`
- `get_commitments_by_article(session, article_code=None) -> list[CommitmentsByArticleItem]` — aggregazione per `article_code` (sum `committed_qty`, count righe)

**Struttura `CommitmentItem`:**
```
article_code, source_type, source_reference, committed_qty, computed_at
```

**Struttura `CommitmentsByArticleItem`:**
```
article_code, total_committed_qty, commitment_count, computed_at
```

**source_reference** per `customer_order`: `"{order_reference}/{line_reference}"` (es. `"ORD001/3"`) — permette di risalire alla riga canonica senza FK persistita.

### Sequenza rebuild

```
rebuild_commitments(session)
  ├─ list_customer_order_lines(session)    — legge Core ordini (da sync_righe_ordine_cliente)
  ├─ filtra open_qty > 0 e article_code not None
  ├─ DELETE all core_commitments
  └─ INSERT CoreCommitment per ogni riga attiva (committed_qty = open_qty)
```

### Test eseguiti

16 test in `tests/core/test_core_commitments.py`:
- committed_qty = open_qty ✓
- source_type = "customer_order" ✓
- source_reference formato "{order_ref}/{line_ref}" ✓
- open_qty = 0 → nessun commitment ✓
- open_qty < 0 (clampato) → nessun commitment ✓
- righe parzialmente chiuse e aperte miste ✓
- righe senza article_code escluse ✓
- aggregazione piu righe stesso articolo ✓
- aggregazione articoli diversi separati ✓
- get_commitments_by_article singolo articolo ✓
- get_commitments_by_article articolo inesistente → [] ✓
- rebuild deterministico ✓
- rebuild ricalcola dopo aggiornamento mirror ✓
- rebuild rimuove commitments di righe chiuse ✓
- mirror vuoto → 0 commitments ✓
- list_commitments con filtro source_type ✓

Suite completa: 416/416 passed.

### Test non eseguiti

- Test HTTP su eventuali endpoint API commitments: non inclusi — il task non introduce API.
- Test con dati reali Easy: non eseguibili senza connessione.

### Assunzioni

- `committed_qty = open_qty` (V1): la quantita gia inscatolata/appartata (`set_aside_qty`) e gia sottratta nell'`open_qty` del Core ordini, quindi non viene doppiamente conteggiata.
- Il rebuild legge dal Core ordini (`list_customer_order_lines`), non direttamente da `sync_righe_ordine_cliente`: la logica `open_qty` e `description_lines` risiede nel Core ordini, non nei commitments.
- `source_reference` e una stringa leggibile (non una FK): permette tracciabilita senza accoppiamento strutturale.
- Il rebuild e delete-all + re-insert (non upsert): deterministico, stesso input stesso output.
- Il chiamante gestisce il commit (come `rebuild_inventory_positions`).

### Limiti noti

- V1 solo `customer_order`: la provenienza `production` e un follow-up (DL-ARCH-V2-017 §3).
- Nessun endpoint API esposto: il contratto e consumabile da moduli futuri via import Python.
- Nessun scheduler automatico del rebuild.
- Il rebuild ha costo O(n) sulle righe ordine attive.

### Follow-up suggeriti

- Commitments da `production` (seconda provenienza, DL-ARCH-V2-017 §3).
- Computed fact `availability = inventory - commitments` (DL-ARCH-V2-017 §8).
- Endpoint `POST /api/core/commitments/rebuild` per trigger manuale.
- Integrazione del rebuild nel flusso `trigger_produzione` (dopo sync righe ordine).
- Surface UI con visualizzazione impegni per articolo.
