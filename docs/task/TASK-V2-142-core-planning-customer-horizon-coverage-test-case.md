# TASK-V2-142 - Core planning: test case customer horizon coverage su 12x8x25

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`
- `docs/task/TASK-V2-139-ui-planning-workspace-filters-scope-customer-horizon-search.md`

## Goal

Formalizzare e verificare con un test mirato il caso reale dell'articolo `12x8x25`, per confermare che la componente cliente del planning:

- rispetta davvero l'`Orizzonte cliente`
- non scatta sul totale aggregato degli impegni futuri
- genera `customer_shortage_qty` solo quando la prima scopertura cade dentro l'orizzonte attivo

## Context

Caso operativo reale osservato in Easy:

- articolo: `12x8x25`
- giacenza iniziale: `4129`
- impegni cliente:
  - `400` con consegna `21/04/2026`
  - `2000` con consegna `05/06/2026`
  - `2000` con consegna `05/07/2026`

Progressione teorica:

- dopo `21/04/2026`: `3729`
- dopo `05/06/2026`: `1729`
- dopo `05/07/2026`: `-271`

Conclusione attesa:

- fino al `05/06/2026` il lato cliente e coperto
- la prima vera scopertura cliente nasce solo al `05/07/2026`

Con `Orizzonte cliente = 30 giorni`, a partire dal contesto temporale del caso, il planning non deve ancora aprire un bisogno cliente.

## Scope

- aggiungere uno o piu test core mirati sul caso `12x8x25`
- verificare il comportamento della componente cliente con `Orizzonte cliente = 30`
- verificare che la componente cliente non usi il totale aggregato `4400` senza cap temporale
- verificare il driver risultante del candidate nel caso in cui resti solo la componente scorta

## Out of Scope

- redesign UI planning
- modifica della stock policy
- modifica dei filtri UI
- proposta/export

## Constraints

### Scenario numerico minimo

Dati:

- `inventory_qty = 4129`
- impegni cliente:
  - `400` il `2026-04-21`
  - `2000` il `2026-06-05`
  - `2000` il `2026-07-05`
- `customer_horizon_days = 30`

Assunzione del test:

- nessuna supply aggiuntiva che alteri il caso

### Esito atteso con `customer_horizon_days = 30`

La componente cliente deve vedere solo l'impegno:

- `400` del `21/04/2026`

Quindi:

- `customer_shortage_qty = 0`

Regole attese:

- non deve emergere shortage cliente dal totale aggregato `4400`
- il candidate non deve essere classificato come `Cliente` in questo orizzonte
- se esiste comunque un candidate, deve derivare dalla sola componente scorta

### Estensione utile del test

E utile aggiungere anche una seconda verifica con orizzonte piu ampio, tale da includere `05/07/2026`, per dimostrare che:

- la componente cliente inizia a scattare solo quando la prima scopertura entra davvero nell'orizzonte

In quel caso l'atteso minimo e:

- `customer_shortage_qty = 271`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No, salvo fix se il test fallisce
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` No
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 08 - Quantita esplicite con semantica distinta`
- `TASK-V2-100`
- `TASK-V2-103`
- `TASK-V2-104`

## Refresh / Sync Behavior

- `Nessun nuovo refresh on demand`
- `Nessun impatto sulla chain di refresh`

## Acceptance Criteria

- esiste almeno un test core che riproduce il caso `12x8x25`
- con `customer_horizon_days = 30`, il test verifica:
  - `customer_shortage_qty = 0`
  - nessuna classificazione cliente anticipata
- con orizzonte che include `05/07/2026`, il test verifica:
  - `customer_shortage_qty = 271`
- se il comportamento attuale del core non rispetta questi attesi:
  - il task include il fix minimo necessario
- la suite mirata planning resta verde

## Deliverables

- test core mirati sul caso reale
- eventuale fix minimo del calcolo customer-driven se il test evidenzia una regressione

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd backend
pip install -e .[dev]
```

## Verification Commands

```bash
cd backend
python -m pytest V2/backend/tests/core/test_core_planning_candidates.py -q
```

Atteso: exit code `0`.

## Implementation Log

### `backend/src/nssp_v2/core/planning_candidates/queries.py`

- il ramo `by_article` non usa piu `future_availability_qty` completo per derivare la sola componente cliente
- introdotta disponibilita dedicata su `customer_horizon_days`
- `customer_shortage_qty` ora reagisce solo agli impegni cliente entro l'orizzonte operativo
- la candidatura by_article non scatta piu automaticamente sul totale aggregato dei commitments futuri:
  - serve shortage cliente entro orizzonte
  - oppure trigger scorta sullo stock horizon

### `backend/tests/core/test_core_planning_candidates_stock_horizon.py`

- aggiunti test mirati sul caso reale `12X8X25`
- verificato:
  - con `customer_horizon_days = 30` il candidate non compare
  - con `customer_horizon_days = 90` `customer_shortage_qty = 271`
