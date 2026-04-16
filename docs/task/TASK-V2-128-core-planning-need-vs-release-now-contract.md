# TASK-V2-128 - Core planning need vs release-now contract

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-040.md`

## Goal

Aprire il primo stream di codice del rebase planning introducendo nel Core il contratto esplicito `need vs release now` per il ramo `Planning Candidates by_article`.

## Context

Oggi `Planning Candidates` espone il bisogno, ma non distingue ancora in modo esplicito:

- quanto manca rispetto al target/bisogno futuro
- quanta quantita e davvero lanciabile ora senza overflow di capienza

Questo produce casi come:

- `required_qty_total > 0`
- magazzino fisico gia quasi pieno
- candidate corretto come need
- ma quantita percepita implicitamente come lanciabile

Il rebase fissa che questa distinzione appartiene a `Planning Candidates`, non a `Production Proposals`.

## Scope

- estendere il read model `Planning Candidates by_article` con:
  - `required_qty_eventual`
  - `capacity_headroom_now_qty`
  - `release_qty_now_max`
  - `release_status`
- mantenere i campi storici attuali per compatibilita:
  - `required_qty_minimum`
  - `required_qty_total`
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `primary_driver`
- introdurre la prima formula di `release now` basata su:
  - `inventory_qty`
  - `capacity_effective_qty`
- aggiungere test backend mirati

## Out of Scope

- redesign UI planning
- nuove proposal logic
- rebase quantitativo completo del ramo `by_customer_order_line`
- scheduling o scoring

## Constraints

Il primo slice vale pienamente solo per:

- `by_article`

Formula iniziale:

```text
required_qty_eventual = required_qty_total
capacity_headroom_now_qty = max(capacity_effective_qty - inventory_qty, 0)
release_qty_now_max = min(required_qty_eventual, capacity_headroom_now_qty)
```

Vocabolario iniziale `release_status`:

- `launchable_now`
- `launchable_partially`
- `blocked_by_capacity_now`

Regole:

- `launchable_now`
  - `release_qty_now_max >= required_qty_eventual`
- `launchable_partially`
  - `0 < release_qty_now_max < required_qty_eventual`
- `blocked_by_capacity_now`
  - `release_qty_now_max = 0` e `required_qty_eventual > 0`

Per `by_customer_order_line` in questo task:

- i campi nuovi possono restare `null` o non valorizzati
- il ramo per-riga non va forzato in un modello di capienza aggregata non ancora deciso

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 08 - Quantita esplicite con semantica distinta`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

Il task modifica solo il contratto Core/read model consumato dalla vista planning.

## Acceptance Criteria

- i candidate `by_article` espongono `required_qty_eventual`
- i candidate `by_article` espongono `capacity_headroom_now_qty`
- i candidate `by_article` espongono `release_qty_now_max`
- i candidate `by_article` espongono `release_status`
- i campi attuali restano disponibili per compatibilita
- i test backend coprono almeno:
  - need positivo e pienamente lanciabile
  - need positivo e lanciabile solo parzialmente
  - need positivo ma bloccato da capienza attuale

## Deliverables

- read model/query Core planning aggiornati
- test backend mirati

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd backend
pip install -e .[dev]
```

## Verification Commands

```bash
python -m pytest V2/backend/tests/core/test_core_planning_candidates.py -q
```

Atteso: exit code `0`.

## Implementation Log

### Logica pura — `core/planning_candidates/logic.py`

Aggiunte in coda al file tre funzioni e il tipo `ReleaseStatus`:

- `ReleaseStatus = Literal["launchable_now", "launchable_partially", "blocked_by_capacity_now"]`
- `capacity_headroom_now_qty_v1(capacity_effective_qty, inventory_qty)` — `max(capacity - inventory, 0)`
- `release_qty_now_max_v1(required_qty_eventual, headroom)` — `min(required, headroom)`
- `release_status_v1(release_qty_now_max, required_qty_eventual)` — classificazione vocabolario

### Read model — `core/planning_candidates/read_models.py`

`PlanningCandidateItem` esteso con 4 campi opzionali (ramo `by_article`, `None` per `by_customer_order_line`):

```python
required_qty_eventual: Decimal | None = None
capacity_headroom_now_qty: Decimal | None = None
release_qty_now_max: Decimal | None = None
release_status: Literal["launchable_now", "launchable_partially", "blocked_by_capacity_now"] | None = None
```

### Query — `core/planning_candidates/queries.py`

In `_list_by_article_candidates`, dopo il calcolo di `req_total`, aggiunto blocco:

```python
capacity_effective_qty = metrics.capacity_effective_qty if metrics else None
if capacity_effective_qty is not None and req_total is not None:
    headroom = capacity_headroom_now_qty_v1(capacity_effective_qty, avail.inventory_qty)
    rel_max = release_qty_now_max_v1(req_total, headroom)
    rel_status = release_status_v1(rel_max, req_total)
else:
    headroom = None; rel_max = None; rel_status = None
```

`required_qty_eventual` è sempre valorizzato a `req_total`. `headroom`/`rel_max`/`rel_status` sono `None` se `capacity_effective_qty` non configurata.

### `__init__.py`

Aggiunte le 3 nuove funzioni a import e `__all__`.

### Test — `tests/core/test_core_planning_candidates.py`

Aggiunte due nuove classi (15 test totali):

- `TestReleaseNowLogicaPura` (11 test): logica pura di `capacity_headroom_now_qty_v1`, `release_qty_now_max_v1`, `release_status_v1`
- `TestReleaseNowIntegrazione` (4 test): integrazione con `list_planning_candidates_v1` — launchable_now, launchable_partially, blocked_by_capacity_now, e campi headroom/max/status None senza capacity configurata

**Esito:** `73 passed` in 1.98s.
