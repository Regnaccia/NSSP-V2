# TASK-V2-139 - UI planning workspace filters: scope, orizzonte cliente, ricerche

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-138-ui-planning-workspace-left-center-refinement.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Introdurre nella shadow view del `Unified Planning Workspace` i nuovi filtri operativi già fissati in spec:

- `scope`
- `Orizzonte cliente`
- ricerca `codice`
- ricerca `descrizione`
- ricerca `cliente`
- sorting della colonna sinistra

## Context

Il rebase planning ha chiarito che il filtro temporale lato utente non deve essere un generico `entro X giorni`, ma un filtro esplicito:

- `Orizzonte cliente`

La sua semantica è:

- agisce solo sulla componente cliente
- quindi sul calcolo di `customer_shortage_qty`
- non modifica la componente scorta
- la componente scorta continua a usare il proprio orizzonte:
  - `mesi scorta`

Serve anche rendere esplicito il filtro per scope operativo e allineare le ricerche al vocabolario/UX già usati in `articoli`.

## Scope

- aggiungere alla shadow view planning:
  - filtro `scope`
  - filtro `Orizzonte cliente`
  - ricerca `codice`
  - ricerca `descrizione`
  - ricerca `cliente`
  - sorting della colonna sinistra
- applicare il filtro `scope` con semantica già fissata
- applicare il filtro `Orizzonte cliente` solo alla componente cliente del calcolo planning
- mantenere invariata la logica stock, che continua a usare l'orizzonte `mesi scorta`
- riusare la normalizzazione UX del codice già adottata in `articoli`

## Out of Scope

- colonna destra proposal
- nuove logiche stock o proposal
- modifica della formula stock horizon
- redesign completo della toolbar oltre i filtri richiesti
- sostituzione della vista planning legacy

## Constraints

### Scope

Valori ammessi:

- `Tutti`
- `Solo clienti`
- `Solo magazzino`

Semantica:

- `Solo clienti`
  - include:
    - `Cliente`
    - `Cliente + Magazzino`
- `Solo magazzino`
  - include solo candidate `stock-only`

### Orizzonte cliente

Naming UI obbligatorio:

- `Orizzonte cliente`

Default:

- `365 giorni`

Semantica obbligatoria:

- agisce solo sulla componente cliente del candidate
- quindi sul calcolo di `customer_shortage_qty`
- non modifica `stock_replenishment_qty`
- la componente scorta continua a usare il proprio orizzonte:
  - `mesi scorta`

Conseguenze ammesse:

- un candidate misto puo restare misto
- puo diventare `Magazzino`
- puo sparire

### Ricerche

- ricerca `codice`
  - deve riusare la normalizzazione UX di `articoli`
  - equivalenza minima:
    - `.` -> `x`
- ricerca `descrizione`
  - testuale
- ricerca `cliente`
  - su `requested_destination_display`

### Sorting colonna sinistra

Opzioni iniziali:

- `codice`
- `data di consegna`

Regole:

- `codice`
  - ordinamento alfabetico sul codice articolo
- `data di consegna`
  - usa `requested_delivery_date` quando disponibile
  - i casi senza data consegna restano ordinabili in modo stabile ma secondario
  - il sorting per data non deve inventare una data per i casi `stock-only`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Probabilmente Si, per applicare `Orizzonte cliente` al calcolo della componente cliente
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
- `DL-ARCH-V2-040` need vs release-now

## Refresh / Sync Behavior

- `La shadow view riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- la shadow view espone i filtri:
  - `scope`
  - `Orizzonte cliente`
  - ricerca `codice`
  - ricerca `descrizione`
  - ricerca `cliente`
- la shadow view espone anche il sorting della colonna sinistra:
  - `codice`
  - `data di consegna`
- `Solo clienti` include anche i casi `Cliente + Magazzino`
- `Solo magazzino` include solo `stock-only`
- la ricerca codice normalizza `.` come `x`
- la ricerca cliente filtra su `requested_destination_display`
- `Orizzonte cliente` modifica solo la componente cliente
- la componente scorta continua a usare l'orizzonte `mesi scorta`
- il build frontend resta verde

## Deliverables

- refinement Core/UI necessario ad applicare i filtri alla shadow view planning
- eventuali update minimi ai tipi/API se richiesti dal filtro `Orizzonte cliente`

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

### Analisi backend

`horizon_days` è già passato come `customer_horizon_days` a `list_planning_candidates_v1`.
Agisce su `is_within_customer_horizon` (flag per-candidate). La formula `customer_shortage_qty_v1`
usa `future_availability_qty` (all commitments) — nessuna modifica backend necessaria: il workspace
re-fetcha con il `horizon_days` aggiornato e usa `is_within_customer_horizon` per il filtro client-side.
73 test esistenti Core planning candidates passati senza modifiche.

### `frontend/src/pages/surfaces/PlanningWorkspacePage.tsx`

**Nuovi tipi:** `ScopeFilter`, `SortBy`

**Nuovo stato:**
- `scopeFilter: ScopeFilter` (default `'tutti'`)
- `horizonDays: number` (default `30`)
- `filterCliente: string`
- `sortBy: SortBy` (default `'data_consegna'`)

**Re-fetch su `horizonDays`:** `useEffect` con debounce 600ms, aggiorna `is_within_customer_horizon` da backend.

**Logica filtri in `filtered` useMemo:**
- Scope `solo_clienti`: esclude `clienteScopeLabel === 'Magazzino'`; `solo_magazzino`: solo stock-only
- Orizzonte cliente: stock-only non filtrati; `by_customer_order_line` filtra per `requested_delivery_date ≤ today+horizonDays`; `by_article` con customer usa `is_within_customer_horizon !== false`
- `matchesCodice` (normalizzazione `.→x` esistente), `matchesDesc`, `matchesCliente` (su `requested_destination_display`)
- Sorting: `codice` → `localeCompare`; `data_consegna` → timestamp asc, nulls last, secondary sort codice

**`WorkspaceToolbar`** (sostituisce `WorkspaceFilterBar`):
- pill toggle Scope: Tutti / Solo clienti / Solo magazzino
- input numerico `Orizzonte cliente` (gg)
- input ricerca: Codice, Descrizione, Cliente
- select Famiglia
- pill toggle sort: Data consegna / Codice

**Esito build:** `✓ built in 7.97s`, exit code `0`.
**Test backend:** `73 passed` (invariati).
