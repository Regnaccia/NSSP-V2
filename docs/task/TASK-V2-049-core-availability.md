# TASK-V2-049 - Core availability

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
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-020.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/task/TASK-V2-037-core-inventory-positions.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`
- `docs/task/TASK-V2-043-commitments-produzione.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`
- `docs/task/TASK-V2-048-allineamento-operativo-righe-ordine-cliente.md`

## Goal

Costruire il fact canonico `availability`, derivato da `inventory`, `customer_set_aside` e `commitments`,
come quota corrente libera per articolo.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-037`
- `TASK-V2-042`
- `TASK-V2-043`
- `TASK-V2-044`
- `TASK-V2-048`

## Context

Con `DL-ARCH-V2-021` la V2 fissa `availability` come computed fact canonico del `core`.

Nel perimetro V1:

- `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`

Questo fact deve:

- consumare solo fact canonici del Core
- restare separato da ATP, allocazioni e planning
- fornire una base riusabile ai moduli futuri

## Scope

### In Scope

- modello Core `availability` o equivalente
- aggregazione minima per `article_code`
- campi canonici minimi:
  - `article_code`
  - `inventory_qty`
  - `customer_set_aside_qty`
  - `committed_qty`
  - `availability_qty`
  - `computed_at`
- uso di `0` per fact mancanti nel calcolo
- query/read model Core consumabile da futuri moduli
- rebuild completo deterministico del fact

### Out of Scope

- UI dedicata `availability`
- integrazione nel dettaglio `articoli`
- refresh sequenziale della surface `articoli`
- ATP
- allocazioni
- priorita
- simulazioni temporali
- multi-magazzino

## Constraints

- il task deve leggere da:
  - `inventory_positions`
  - `customer_set_aside`
  - `commitments`
- non deve leggere dai mirror sync grezzi
- `availability_qty` puo risultare negativa
- il calcolo deve essere deterministico a parita di input
- `free_stock` non deve essere materializzato come fact canonico separato

## Acceptance Criteria

- esiste un computed fact `availability` o equivalente
- `availability_qty` e calcolata come:
  - `inventory_qty - customer_set_aside_qty - committed_qty`
- i fact mancanti per articolo valgono `0`
- il rebuild completo e deterministico
- esiste almeno una query/read model per `article_code`
- `python -m pytest tests -q` passa

## Deliverables

- modelli/query/read model `availability`
- migration necessaria, se prevista dal modello scelto
- command o job interno di rebuild del fact
- test backend minimi su:
  - formula di calcolo
  - uso di `0` per fact mancanti
  - valori negativi ammessi
  - aggregazione per articolo
  - determinismo del rebuild

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica coerente del rebuild `availability`.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- query/read model introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- trattare `availability` come fact derivato puro del `core`
- usare una strategia `delete-all + re-insert` per il V1
- mantenere visibili nel modello anche i tre contributi numerici a monte
- non introdurre clamp a zero

## Follow-up attesi

Dopo questo task, i passi naturali sono:

- esposizione read-only di `availability` nel dettaglio `articoli`
- estensione del refresh sequenziale `articoli` per ricalcolare anche `availability`
- futura UI dedicata o filtri basati su `availability`

## Completion Notes

### File creati

- `src/nssp_v2/core/availability/__init__.py` — package
- `src/nssp_v2/core/availability/models.py`
  - `CoreAvailability`: `id`, `article_code` (UniqueConstraint), `inventory_qty`, `customer_set_aside_qty`, `committed_qty`, `availability_qty`, `computed_at`
- `src/nssp_v2/core/availability/read_models.py`
  - `AvailabilityItem`: read model frozen Pydantic, stessi campi del modello ORM
- `src/nssp_v2/core/availability/queries.py`
  - `rebuild_availability(session) -> int`: delete-all + re-insert; aggrega i tre fact via dict in memoria; union degli article_code attivi; no clamp; ritorna numero righe create; no commit
  - `list_availability(session)`: lista ordinata per article_code
  - `get_availability(session, article_code)`: singolo articolo o None
- `alembic/versions/20260409_017_core_availability.py`
  - revision=`20260409017`, down_revision=`20260409016`
  - crea `core_availability` con UniqueConstraint su `article_code`
- `tests/core/test_core_availability.py` — 14 test
- `scripts/rebuild_availability.py` — CLI on-demand

### Migration introdotta

- `20260409_017_core_availability.py`: crea `core_availability` (una riga per `article_code`)

### Query/read model introdotti

- `rebuild_availability`: strategia full rebuild (delete-all + re-insert); aggrega inventory, set_aside e committed via dict; usa `_ZERO` per fact mancanti; union degli article_code per coprire articoli presenti in un solo fact
- `list_availability` / `get_availability`: read model canonico per consumatori futuri
- `AvailabilityItem`: Pydantic frozen, contratto stabile tra Core e moduli applicativi

### Test eseguiti (14/14 passed)

| Test | Verifica |
|---|---|
| `test_formula_canonica` | formula base: 100 - 15 - 30 = 55 |
| `test_availability_negativa_ammessa` | 10 - 20 - 50 = -60, no clamp |
| `test_solo_inventory_*` | set_aside=0, committed=0 quando assenti |
| `test_solo_set_aside_*` | inventory=0, committed=0 quando assenti |
| `test_solo_committed_*` | inventory=0, set_aside=0 quando assenti |
| `test_tutti_zero_nessun_articolo` | mirror vuoti -> 0 righe |
| `test_piu_commitment_stesso_articolo_aggregati` | aggregazione multi-riga committed |
| `test_piu_set_aside_stesso_articolo_aggregati` | aggregazione multi-riga set_aside |
| `test_articoli_distinti_trattati_separatamente` | 2 articoli -> 2 righe indipendenti |
| `test_rebuild_deterministico` | doppio rebuild -> stesso risultato |
| `test_rebuild_aggiorna_dopo_modifica_sorgente` | aggiunta set_aside ricalcolata |
| `test_rebuild_rimuove_articolo_non_piu_presente` | svuotamento sorgenti -> 0 righe |
| `test_get_availability_articolo_assente` | None per articolo inesistente |
| `test_list_availability_ordinata_per_article_code` | ordinamento alfabetico |

Suite completa: 482/482 passed.

### Test non eseguiti

- Test HTTP end-to-end: non inclusi (`availability` non ha ancora un endpoint API — fuori scope)
- Test con dati reali: non eseguibili senza connessione Easy

### Assunzioni

- I fact sorgente (`inventory_positions`, `customer_set_aside`, `commitments`) sono già materializzati prima del rebuild `availability`. Il chiamante è responsabile della sequenza.
- L'aggregazione avviene in memoria Python (non in SQL) per semplicità e leggibilità. Per dataset molto grandi potrebbe diventare un bottleneck, ma è accettabile nel V1.
- `availability_qty` su articoli presenti solo in un fact è negativa o pari all'inventory: comportamento corretto e documentato.

### Limiti noti

- `availability` non è ancora esposta nella surface `articoli` (fuori scope TASK-V2-049)
- Il refresh sequenziale della surface `articoli` non include ancora `rebuild_availability` (fuori scope)
- Nessun endpoint API dedicato: il fact è consumabile solo via query Core interna

### Follow-up suggeriti

- TASK-V2-050: esposizione read-only di `availability` nel dettaglio `articoli`
- TASK-V2-051: estensione del refresh sequenziale `articoli` per includere `rebuild_availability` come step 6

## Completed At

2026-04-09

## Completed By

Claude Code
