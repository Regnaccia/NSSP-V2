# TASK-V2-137 - UI planning unified workspace shadow view left + center

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-041.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`

## Goal

Introdurre una nuova vista UI parallela per validare il target `Unified Planning Workspace` senza sostituire subito la surface corrente `Planning Candidates`.

Questo primo slice deve implementare soltanto:

- colonna sinistra
- colonna centrale

La colonna destra proposal resta esplicitamente fuori scope e verra progettata/implementata in uno slice successivo.

## Context

Il rebase architetturale ha fissato che:

- `Planning Candidates` deve diventare la surface operativa primaria
- la proposal va resa come pannello contestuale, non come seconda pagina primaria

Prima di costruire la colonna destra, conviene validare con gli operatori la nuova interaction architecture su:

- inbox sintetica a sinistra
- dettaglio candidato al centro

Per ridurre il rischio di regressione, la vista attuale `Planning Candidates` deve restare disponibile per confronto.

## Scope

- creare una nuova vista UI parallela / shadow view del planning workspace
- mantenere la vista `Planning Candidates` attuale disponibile e invariata
- implementare nella nuova vista:
  - colonna sinistra secondo il contratto UIX congelato
  - colonna centrale secondo il contratto UIX congelato
- riusare i read model Core esistenti, senza introdurre ancora la colonna destra proposal
- supportare selezione riga/articolo tra sinistra e centro

## Out of Scope

- colonna destra proposal
- batch export
- override proposta
- nuova logica proposal
- rimozione o sostituzione della vista planning attuale
- migrazione completa del routing finale

## Constraints

Regole:

- la nuova vista deve convivere con la view planning attuale
- la view attuale resta il riferimento operativo durante il confronto
- la shadow view deve consumare i contratti Core gia disponibili
- nessun nuovo contratto backend e richiesto in questo task salvo minimi adattamenti di presentazione strettamente necessari
- la colonna sinistra deve rispettare il contratto gia congelato:
  - `cliente_scope_label`
  - `article_code`
  - `display_description`
  - `measure`
  - `requested_delivery_date` solo se customer
  - `release_status`
  - `proposal_status`
  - `workflow_status`
  - `priority_score` placeholder
  - triangolo warning minimo
- la colonna centrale deve rispettare i blocchi gia congelati:
  - `Identita`
  - `Need vs Release`
  - `Motivo`
  - `Cliente / Ordine`
  - `Stock / Capienza`
  - `Warnings`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No, salvo minimi adattamenti UI-facing strettamente necessari
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 09 - Una surface per dominio, non per query locale`
- `DL-UIX-V2-002` pattern multi-colonna

## Refresh / Sync Behavior

- `La nuova vista riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- esiste una nuova vista planning parallela alla corrente
- la vista planning attuale resta disponibile per confronto
- la shadow view implementa la colonna sinistra secondo la spec UIX congelata
- la shadow view implementa la colonna centrale secondo la spec UIX congelata
- selezionando un candidate a sinistra, il centro mostra il dettaglio coerente
- il build frontend resta verde

## Deliverables

- nuova shadow view UI del planning workspace
- eventuale route o access point di confronto
- aggiornamenti docs minimi se il naming della view va esplicitato

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
cd frontend
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### `frontend/src/pages/surfaces/PlanningWorkspacePage.tsx`

Nuova shadow view a 2 colonne attive (colonna destra fuori scope):

**Colonna sinistra (w-72) — inbox sintetica:**
- Card per candidate con gerarchia visiva della spec: `ProposalStatusBadge` → `WorkflowStatusBadge` → `ReleaseStatusBadge` → scope + codice + ▲ warning → descrizione → misura + data + qty
- `proposal_status` derivato da `release_status` (backend non espone ancora il campo): `launchable_now` → `valid_for_export`, `launchable_partially` → `need_review`, `blocked_by_capacity_now` → `error`
- `workflow_status` sempre `inattivo` (workspace state non ancora persistito nel backend)
- `cliente_scope_label` derivato da `primary_driver` + `customer_shortage_qty` / `stock_replenishment_qty`
- Ordinamento: `required_qty_minimum` decrescente

**Colonna centrale (flex-1) — 6 blocchi da spec:**
1. `Identità`: codice, scope badge, famiglia, descrizione, misura
2. `Need vs Release`: ramo by_article (shortage/replenishment/eventual/release_now) o by_customer_order_line (line_demand/linked_supply/coverage/min)
3. `Motivo`: primary_driver badge, reason_code, reason_text
4. `Cliente / Ordine`: solo se customer component — data, destinazione, ordine/riga, descrizione riga
5. `Stock / Capienza`: solo by_article — availability, headroom, supply, future_availability
6. `Warnings`: lista warning attivi o stato "Nessun warning"

**Filter bar:** codice, descrizione, famiglia, solo perimetro produzione

### `frontend/src/App.tsx`
- Aggiunta route `/produzione/planning-workspace` → `PlanningWorkspacePage` (roles: produzione)

### `frontend/src/components/AppShell.tsx`
- Aggiunta voce `Workspace (β)` nel sotto-menu `produzione`
- La voce `Planning` (tabella attuale) resta invariata per confronto

**Esito build:** `✓ built in 7.43s`, exit code `0`.

