# TASK-V2-114 - Core articoli case-insensitive code bridge planning->articoli

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date
2026-04-14

## Owner
Claude Code

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md`

## Goal

Allineare il lookup e la configurazione articolo al codice canonical usato nel planning, senza
rompere la semantica dei codici raw in `sync_articoli`.

## Context

`Planning Candidates` espone `article_code` normalizzato (uppercase), mentre il dominio `articoli`
lavora con il codice raw in `sync_articoli`/`core_articolo_config`.

Questo causava mismatch operativi:

- `GET /api/produzione/articoli/{codice}` poteva dare 404 con codice canonical
- quick config da planning poteva non trovare/aggiornare la config articolo attesa

## Scope

- introdurre nel Core `articoli` una risoluzione codice article case-insensitive verso `sync_articoli`
- applicare il bridge a:
  - lookup dettaglio articolo
  - write di configurazione articolo (famiglia/policy/stock/gestione scorte)
- aggiungere test mirati di regressione

## Out of Scope

- cambi di normalizzazione in `sync_articoli`
- modifiche al contratto API di `articoli`
- modifiche al contratto `planning candidates`

## Constraints

- nessuna duplicazione di record in `core_articolo_config` per differenze di casing
- preservare il codice raw come chiave effettiva del dominio `articoli`
- accettare in input anche codici canonical provenienti da planning

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `No`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `No`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `No`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Pattern References

- `Pattern 2 - Mirror esterno + arricchimento interno`
- `Pattern 16 - Core unico, segmentazione solo in UI`

## Refresh / Sync Behavior

La vista riusa refresh semantici backend gia esistenti.

Il fix non introduce o modifica chain di refresh.

## Acceptance Criteria

- `GET /api/produzione/articoli/{codice}` risolve codice articolo in modo case-insensitive
- set configurazione articolo via endpoint `articoli/*` usa la PK raw corretta anche con input canonical
- nessuna duplicazione di config articolo per lo stesso codice con casing differente

## Deliverables

- bridge case-insensitive nel Core `articoli`
- test Core mirati su lookup e set config

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q tests/core/test_core_articoli.py tests/core/test_core_famiglia_articoli.py
```

Expected: exit code 0, test mirati passati.

## Implementation Notes

- introdotto helper dedicato `_resolve_sync_articolo_code` in `core/articoli/queries.py`
- applicato sia al lookup dettaglio sia alle write di configurazione
- mantenuta la semantica raw per `codice_articolo` in `core_articolo_config`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

### Summary

Implementato bridge case-insensitive tra codici canonical (planning) e codici raw (`sync_articoli`)
nel dominio `articoli`.

### Files Changed

- `backend/src/nssp_v2/core/articoli/queries.py` - aggiunto resolver codice e wiring su lookup/write
- `backend/tests/core/test_core_articoli.py` - test lookup case-insensitive
- `backend/tests/core/test_core_famiglia_articoli.py` - test write config con input canonical

### Contracts / Flows Changed

- invariati endpoint e payload
- cambiata la risoluzione interna del parametro `codice_articolo`:
  - da match esatto
  - a match esatto + fallback case-insensitive su `sync_articoli`

### Dependencies Introduced

- Nessuna

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest -q tests/core/test_core_articoli.py tests/core/test_core_famiglia_articoli.py` | Claude Code (agente) | venv locale backend | 34 passed |

### Assumptions

- nel dataset operativo non esistono codici articolo distinti solo per casing

### Known Limits

- in caso teorico di collisione case-insensitive, viene selezionato il primo codice ordinato alfabeticamente

### Documentation Impact

- `docs/task/README.md` (indice task)
- `docs/roadmap/TASK_LOG.md`

### Follow-ups

- valutare hardening con warning dedicato se mai emergono collisioni case-insensitive su `sync_articoli`

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)

