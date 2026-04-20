# TASK-V2-140 - UI planning workspace: parametri di calcolo + scheda destra Planning / Scorte

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-138-ui-planning-workspace-left-center-refinement.md`
- `docs/task/TASK-V2-139-ui-planning-workspace-filters-scope-customer-horizon-search.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`

## Goal

Completare il primo slice cross-column del `Unified Planning Workspace` introducendo:

- in colonna centrale:
  - blocco read-only `Parametri di calcolo`
- in colonna destra:
  - scheda editabile `Planning / Scorte`

con navigazione esplicita:

- CTA `Override` dal blocco centrale
- apertura contestuale della scheda destra senza modal

## Context

La review UX ha chiarito il confine corretto:

- colonna sinistra:
  - inbox sintetica
- colonna centrale:
  - comprensione e validazione
- colonna destra:
  - azione e configurazione

Di conseguenza, i parametri che influenzano il planning devono essere:

- spiegati al centro come valori effettivi e derivati
- editati a destra solo dove sono davvero configurabili

## Scope

- aggiungere alla colonna centrale il blocco `Parametri di calcolo`
- mostrare i valori effettivi e derivati concordati in spec
- mostrare la provenienza dei parametri quando applicabile
- aggiungere la CTA `Override`
- introdurre nella colonna destra la scheda `Planning / Scorte`
- rendere editabili nella scheda destra solo i parametri planning/scorte concordati
- collegare la CTA `Override` all'apertura della scheda destra corretta

## Out of Scope

- pannello proposal della colonna destra
- batch export
- override qty proposal
- configurazione `monthly_base_strategy_key`
- parametri numerici interni della strategy stock
- parametri proposal:
  - `proposal_logic_key`
  - `proposal_logic_article_params`
  - `raw_bar_length_mm`
  - `bar_multiple`
- sostituzione della view planning legacy

## Constraints

### Colonna centrale - Blocco `Parametri di calcolo`

Il blocco deve essere:

- read-only
- visibile nel ramo `by_article`
- nascosto nel ramo `by_customer_order_line` nel primo slice

Campi obbligatori:

- `effective_gestione_scorte_attiva`
- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`
- `monthly_stock_base_qty`
- `target_stock_qty`
- `trigger_stock_qty`
- `customer_horizon_days`
  - come valore attuale del filtro/workspace

Provenienza da mostrare almeno per:

- `effective_gestione_scorte_attiva`
- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`

Vocabolario provenienza ammesso:

- `default famiglia`
- `override articolo`
- `calcolato`
- `workspace`

CTA obbligatoria:

- `Override`

Effetto della CTA:

- non apre un modal
- attiva la colonna destra sulla scheda `Planning / Scorte`

### Colonna destra - Scheda `Planning / Scorte`

Campi editabili obbligatori:

- `planning_mode`
- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`
- `capacity_override_qty`

Regole:

- la scheda destra deve riusare i contract gia esistenti della surface `articoli`
- la colonna centrale resta solo read-only
- nessun dominio parallelo di configurazione

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Probabilmente Si, se servono provenance fields non ancora esposti
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No, riusa quelli esistenti
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

- la colonna centrale mostra il blocco `Parametri di calcolo` nel ramo `by_article`
- il blocco e read-only
- il blocco mostra tutti i campi concordati
- il blocco mostra la provenienza minima concordata
- il blocco espone la CTA `Override`
- la CTA `Override` apre la colonna destra sulla scheda `Planning / Scorte`
- la colonna destra rende editabili:
  - `planning_mode`
  - `gestione_scorte_attiva`
  - `stock_months`
  - `stock_trigger_months`
  - `capacity_override_qty`
- la scheda destra non introduce campi proposal
- il build frontend resta verde

## Deliverables

- refinement UI della shadow view planning
- eventuale estensione minima del read model/API per provenance e parametri effettivi non ancora disponibili

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

### `frontend/src/pages/surfaces/PlanningWorkspacePage.tsx`

**Nuovi tipi:** `RightPanel = 'none' | 'planning_scorte'`

**Nuovo stato:**
- `selectedDetail: ArticoloDetail | null` — caricato da `GET /produzione/articoli/{article_code}` al cambio selezione
- `detailLoading: boolean`
- `rightPanel: RightPanel` (default `'none'`)

**`useEffect` su `selectedItem?.article_code`:** carica `ArticoloDetail` silenziosamente; resetta `rightPanel` a `'none'` al cambio selezione.

**`handleSelectCandidate`:** wrappa `setSelectedId` resettando anche `rightPanel`.

**Provenance helpers:**
- `provenanceStockParam(overrideVal, famigliaCode)` → "override articolo" | "default famiglia" | "—"
- `provenanceCapacity(capacityOverrideQty)` → "override articolo" | "calcolato"
- `ProvenancePill` — badge visivo per la provenienza
- `FieldRowProvenance` — campo con pill provenienza + valore

**`BloccoParametriDiCalcolo` (blocco 5b, solo by_article):**
- Mostra skeleton/messaggio mentre `detailLoading`
- Campi con provenienza: `effective_gestione_scorte_attiva`, `effective_stock_months`, `effective_stock_trigger_months`, `capacity_effective_qty`
- Campi read-only: `monthly_stock_base_qty`, `target_stock_qty`, `trigger_stock_qty`
- `customer_horizon_days` con provenienza "workspace" (valore dal filtro attivo)
- CTA `Override` → `setRightPanel('planning_scorte')` (solo se `selectedDetail` disponibile)

**`PannelloPlanningScorte` (colonna destra):**
- Campi editabili: `planning_mode`, `gestione_scorte_attiva` (override), `stock_months`, `stock_trigger_months`, `capacity_override_qty`
- Placeholder degli input mostra il valore effettivo famiglia/calcolato
- Salvataggio sequenziale su 3 endpoint: `policy-override` → `gestione-scorte-override` → `stock-policy-override`
- Dopo il salvataggio ricarica `ArticoloDetail` e chiama `onSaved` aggiornando `selectedDetail`
- `planning_mode` mappato a `override_aggrega_codice_in_produzione` (by_article → true, by_customer_order_line → false)

**Layout colonne aggiornato:**
- Colonna centrale: `flex-1` → `w-[46%] shrink-0` quando `rightPanel !== 'none'`
- Colonna destra: `flex-1` visibile solo quando `rightPanel === 'planning_scorte' && selectedDetail !== null`

**Esito build:** `✓ built in 7.24s`, exit code `0`.
**Test backend:** invariati (nessuna modifica backend).

