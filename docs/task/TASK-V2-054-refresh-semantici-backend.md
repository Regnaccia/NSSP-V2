# TASK-V2-054 - Refresh semantici backend con dipendenze interne

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/task/TASK-V2-053-refresh-sequenziale-articoli-con-commitments.md`

## Goal

Introdurre nel backend refresh semantici che incapsulino internamente le dipendenze di sync e rebuild, cosi da evitare che UI e router debbano conoscere ogni volta la chain tecnica completa.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-053`

## Context

La surface `articoli` richiede ormai una chain tecnica non banale:

1. `sync_articoli`
2. `sync_mag_reale`
3. `sync_righe_ordine_cliente`
4. `sync_produzioni_attive`
5. `rebuild_inventory_positions`
6. `rebuild_customer_set_aside`
7. `rebuild_commitments`
8. `rebuild_availability`

Questa conoscenza non deve restare replicata:

- nella UI
- negli endpoint
- nella documentazione operativa

Il backend deve esporre un refresh logico unico, con dipendenze interne e comportamento coerente sugli errori.

## Scope

### In Scope

- introdurre nel backend funzioni di refresh semantiche
- spostare la definizione delle dipendenze dentro tali funzioni
- mantenere output tracciabile step-by-step
- applicare `fail-fast` o `skip downstream on failed prerequisite`
- far invocare gli endpoint UI ai refresh semantici invece di orchestrare direttamente la lista step
- aggiornare la documentazione del pattern

### Out of Scope

- scheduler automatico
- parallelizzazione dei refresh
- lock distribuito multi-process
- nuove surface UI
- refactor generale di tutti i moduli in un unico task monolitico

## Constraints

- la UI continua a inviare una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- gli step downstream non partono se un prerequisito fallisce
- la risposta resta leggibile e tracciabile per singolo step
- nessuna scrittura verso Easy

## Acceptance Criteria

- esiste almeno un refresh semantico backend per la surface `articoli`
- il refresh semantico `articoli` incapsula internamente la chain completa delle sue dipendenze
- gli endpoint non duplicano piu la lista completa degli step orchestrati
- in caso di fallimento di uno step prerequisito, gli step dipendenti risultano saltati o non eseguiti
- la risposta backend continua a mostrare il dettaglio step-by-step
- `python -m pytest tests -q` passa
- `npm run build` passa se il task tocca il contratto UI o gli endpoint usati dal frontend

## Deliverables

- refactor backend dell'orchestrazione refresh
- eventuali helper/service dedicati ai refresh semantici
- eventuali test backend coerenti col nuovo pattern
- aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/guides/IMPLEMENTATION_PATTERNS.md`
  - `docs/SYSTEM_OVERVIEW.md`

## Verification Level

`Full suite / milestone`

Questo task e una milestone di consolidamento architetturale del backend refresh.

Quindi:

- richiede full suite backend obbligatoria
- richiede build frontend obbligatoria se il contratto dei refresh o la UI associata vengono toccati
- puo assorbire la verifica finale del fix operativo introdotto in `TASK-V2-053`

## Verification Commands

```bash
cd backend
python -m pytest tests -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- introdurre refresh logici nominati per contesto, non per lista step
- mantenere separato il concetto di:
  - step tecnico
  - refresh semantico
- fare partire dal caso `articoli`, poi estendere il pattern alle altre surface se utile

---

## Completion Notes

### File creati

- `src/nssp_v2/app/services/refresh_articoli.py` (nuovo)
  - `ARTICOLI_SYNC_ENTITIES`: lista delle 4 entita sync della surface articoli
  - `_skipped_result(entity_code)`: produce `EntityRunResult` con `status="skipped"`
  - `_run_rebuild(entity_code, rebuild_fn, session)`: wrapper generico per qualsiasi rebuild Core (try/commit/rollback)
  - `_run_inventory_rebuild(session)`: chiama `_run_rebuild("inventory_positions", ...)`
  - `_run_set_aside_rebuild(session)`: chiama `_run_rebuild("customer_set_aside", ...)`
  - `_run_commitments_rebuild(session)`: chiama `_run_rebuild("commitments", ...)`
  - `_run_availability_rebuild(session)`: chiama `_run_rebuild("availability", ...)`
  - `refresh_articoli(session, conn_string) -> list[EntityRunResult]`: refresh semantico completo — 8 step con dipendenze condizionali

### File modificati

- `src/nssp_v2/app/api/sync.py`
  - Rimossi: tutti i helper rebuild inline (`_run_inventory_rebuild`, `_run_set_aside_rebuild`, `_run_commitments_rebuild`, `_run_availability_rebuild`, `_skipped_result`), `_PRODUZIONE_ENTITIES`, imports delle sorgenti Easy e dei rebuild Core
  - Aggiunto import: `from nssp_v2.app.services.refresh_articoli import ARTICOLI_SYNC_ENTITIES, SyncAlreadyRunningError, refresh_articoli`
  - `trigger_produzione`: ridotto a 5 righe operative (check config + try/except su `refresh_articoli`)
  - `freshness_produzione`: ora usa `ARTICOLI_SYNC_ENTITIES` importato
  - Docstring modulo aggiornata: pattern DL-ARCH-V2-022 documentato

- `tests/unit/test_set_aside_rebuild_helper.py`
  - Import aggiornato: da `nssp_v2.app.api.sync` a `nssp_v2.app.services.refresh_articoli`

- `tests/app/test_sync_produzione_helpers.py`
  - Import aggiornato: tutti gli helper da `nssp_v2.app.services.refresh_articoli`

- `docs/guides/IMPLEMENTATION_PATTERNS.md`
  - Aggiunto Pattern 13: Refresh semantici backend con dipendenze interne

- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - Aggiornato "Stato coperto", endpoint, script on-demand e smoke flow

- `docs/SYSTEM_OVERVIEW.md`
  - Aggiunta sezione Pattern 13, aggiornato "Stato attuale"

- `docs/roadmap/STATUS.md`
  - Aggiornato task completati (`TASK-V2-001` → `TASK-V2-054`), Task aperti: Nessuno

### Architettura risultante

**Prima (TASK-V2-053):**
- `trigger_produzione` orchestrava direttamente 8 step: 4 sync unit + 4 rebuild Core con logica condizionale inline (~40 righe)

**Dopo (TASK-V2-054):**
- `trigger_produzione` chiama `refresh_articoli(session, conn_string)` — 5 righe operative
- Tutta la chain vive in `refresh_articoli.py`, l'unico posto da modificare quando la chain evolve
- `_run_rebuild` generico elimina la ripetizione del pattern try/commit/rollback (era 4x ~15 righe ciascuno)

### Pattern `_run_rebuild` generico

Il wrapper generico:
```python
def _run_rebuild(entity_code, rebuild_fn, session) -> EntityRunResult:
    try:
        n = rebuild_fn(session)
        session.commit()
        return EntityRunResult(entity_code=entity_code, status="success", rows_written=n, ...)
    except Exception as exc:
        session.rollback()
        return EntityRunResult(entity_code=entity_code, status="error", error_message=str(exc), ...)
```

Sostituisce 4 funzioni helper quasi identiche. I 4 helper nominati (`_run_inventory_rebuild`, etc.) restano per testabilita individuale.

### Test eseguiti

- `python -m pytest tests -q`: 507/507 passed (full suite)
- `npm run build`: zero errori

### Assunzioni

- `SyncAlreadyRunningError` viene re-esportato da `refresh_articoli.py` tramite `# noqa: F401` per permettere al router di importarlo da un unico punto. Il router non dipende direttamente da `sync_runner`.
- I test che testano gli helper individualmente (`test_set_aside_rebuild_helper.py`) restano validi: i named wrappers sono ancora esportati dal modulo `refresh_articoli`.

### Limiti noti

- `refresh_articoli` non e testabile in isolamento con fake sources senza un override di dipendenza. I test coprono gli helper individualmente e la logica condizionale di skip. Il test end-to-end dell'endpoint richiede TestClient + auth — fuori scope V1.
- Manca uno script `rebuild_commitments.py` on-demand (analogo a `rebuild_inventory_positions.py`).

### Follow-up suggeriti

- Aggiungere `rebuild_commitments.py` script on-demand
- Estendere il pattern `refresh_semantico` alle altre surface se emergono chain composite simili
- Scheduler automatico dei refresh

## Completed At

2026-04-09

## Completed By

Claude Code
