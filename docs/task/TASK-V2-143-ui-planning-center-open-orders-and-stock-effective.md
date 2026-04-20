# TASK-V2-143 - UI planning center: ordini aperti e giacenza effettiva

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/task/TASK-V2-138-ui-planning-workspace-left-center-refinement.md`
- `docs/task/TASK-V2-139-ui-planning-workspace-filters-scope-customer-horizon-search.md`

## Goal

Rifinire la colonna centrale del `Unified Planning Workspace` introducendo:

- nella sezione `Cliente / Ordine`:
  - sottosezione `Ordini aperti`
  - distinzione visiva `entro orizzonte` / `oltre orizzonte`
- nella sezione `Stock / Capienza`:
  - visualizzazione della `giacenza effettiva` di planning

## Context

La lettura del candidate by-article richiede oggi piu contesto operativo:

- non basta vedere un solo riferimento cliente/ordine
- serve vedere la distribuzione reale degli ordini aperti nel tempo
- serve distinguere cio che ricade entro l'`Orizzonte cliente` da cio che resta oltre

In parallelo, il blocco `Stock / Capienza` deve essere coerente con il planning:

- non mostrare la giacenza raw
- mostrare la giacenza effettiva usata dal Core:
  - `stock_effective_qty = max(inventory_qty, 0)`

## Scope

- estendere il blocco `Cliente / Ordine` del ramo `by_article` con la sottosezione `Ordini aperti`
- mostrare solo righe ordine ancora aperte
- calcolare `open_qty` tenendo conto della quantita appartata
- distinguere visivamente ordini:
  - `entro orizzonte`
  - `oltre orizzonte`
- aggiornare `Stock / Capienza` per mostrare `stock_effective_qty`

## Out of Scope

- modifica del pannello destro
- modifica delle formule planning
- modifica dei filtri toolbar
- redesign della vista planning legacy

## Constraints

### Sottosezione `Ordini aperti`

Perimetro:

- solo nel ramo `by_article`
- non nel ramo `by_customer_order_line`

Riga aperta:

```text
open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```

Campi minimi per riga:

- `requested_delivery_date`
- `order_reference`
- `requested_destination_display`
- `open_qty`

Regole:

- ordinamento per `requested_delivery_date` crescente
- distinzione visiva basata su `customer_horizon_days` attuale del workspace:
  - `entro orizzonte`
  - `oltre orizzonte`

### Blocco `Stock / Capienza`

Il campo principale non deve essere:

- `inventory_qty` raw

Ma:

- `stock_effective_qty`

Formula attesa:

```text
stock_effective_qty = max(inventory_qty, 0)
```

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Probabilmente Si, se la shadow view non riceve ancora lista ordini aperti / stock_effective_qty
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
- `DL-UIX-V2-002` pattern multi-colonna

## Refresh / Sync Behavior

- `La view riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- il blocco `Cliente / Ordine` mostra la sottosezione `Ordini aperti` nel ramo `by_article`
- ogni riga usa `open_qty` calcolata tenendo conto di `set_aside_qty`
- le righe sono ordinate per data consegna
- le righe distinguono visivamente:
  - `entro orizzonte`
  - `oltre orizzonte`
- il blocco `Stock / Capienza` mostra `stock_effective_qty`
- la UI non mostra la giacenza raw negativa nel centro
- il build frontend resta verde

## Deliverables

- refinement Core/UI necessario a popolare e rendere la nuova sottosezione `Ordini aperti`
- refinement UI del blocco `Stock / Capienza`

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
cd ../backend
pip install -e .[dev]
```

## Verification Commands

```bash
cd backend
python -m pytest V2/backend/tests/core/test_core_planning_candidates.py -q

cd ../frontend
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### 2026-04-17

**Backend — `core/planning_candidates/read_models.py`**

- Aggiunto `PlanningOpenOrderLine` (frozen Pydantic model): `order_reference`, `line_reference`, `requested_delivery_date`, `requested_destination_display`, `open_qty`.
- Aggiunto a `PlanningCandidateItem`:
  - `stock_effective_qty: Decimal | None = None` — giacenza effettiva di planning = `max(inventory_qty, 0)`, distinta da `availability_qty`.
  - `open_order_lines: list[PlanningOpenOrderLine]` — lista righe aperte per il ramo `by_article`.

**Backend — `core/planning_candidates/queries.py`**

- In `_list_by_article_candidates`: i `readability_contexts` già caricati per il ramo `by_customer_order_line` vengono riusati per il ramo `by_article`.
- Filtro: `ctx.article_code == avail.article_code and ctx.open_qty > 0`.
- Ordinamento: `requested_delivery_date` crescente (None in fondo).
- Passati `stock_effective_qty=stock_eff` e `open_order_lines=open_lines` al costruttore di `PlanningCandidateItem`.

**Frontend — `types/api.ts`**

- Aggiunta interfaccia `PlanningOpenOrderLine`.
- Aggiunto a `PlanningCandidateItem`: `stock_effective_qty: string | null`, `open_order_lines: PlanningOpenOrderLine[]`.

**Frontend — `PlanningWorkspacePage.tsx`**

- `BloccoClienteOrdine`: firma aggiornata a `{ item, horizonDays }`, container `space-y-3`, chiama `<BloccoOrdiniAperti>` per `by_article` quando `open_order_lines.length > 0`.
- `BloccoOrdiniAperti` (nuovo componente): righe colorate blu (entro orizzonte) / ambra (oltre orizzonte) / neutro (senza data); legenda orizzonte in fondo.
- `BloccoStockCapienza`: prima riga `Giacenza effettiva` (`stock_effective_qty`), seconda riga `Disp. netta` (`availability_qty`). Rimosso `inventory_qty` raw.
- `CenterColumn`: passa `horizonDays` a `BloccoClienteOrdine`.

**Verifica**

- `python -m pytest tests/core/test_core_planning_candidates.py -q` → 73 passed
- `npm run build` → build verde (441 kB JS, 0 errori TypeScript)
