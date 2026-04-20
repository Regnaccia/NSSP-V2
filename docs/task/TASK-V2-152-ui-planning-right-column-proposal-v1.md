# TASK-V2-152 - UI planning right column `Proposal` V1

## Status
Completed

## Date
2026-04-20

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/task/TASK-V2-151-core-proposal-panel-contracts.md`

## Goal

Implementare il primo slice della colonna destra `Proposal` nel workspace planning, senza override.

## Scope

- header proposta
- quantita proposta
- logica proposal
- output export minimo
- diagnostica locale
- azioni minime:
  - `Aggiungi al batch export`
  - `Rimuovi dal batch`

## Out of Scope

- override quantita
- cambio logica manuale
- editing params
- export diretto dal pannello
- batch editor multi-riga

## Acceptance Criteria

- la colonna destra rende i blocchi definiti nella spec UIX
- il pannello resta contestuale al candidate selezionato
- il pannello non duplica il dettaglio planning della colonna centrale
- nessun controllo di override compare nel V1

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-20

TypeScript pulito.

**`PlanningWorkspacePage.tsx`**:
- `RightPanel` esteso a `'none' | 'planning_scorte' | 'proposal'`
- Import aggiunto: `proposalLogicMeta` da `@/lib/proposalLogicMeta`
- Aggiunto `BackendProposalStatusBadge` — consuma il vocabolario backend `Error | Need review | Valid for export`
- Aggiunto `PannelloProposal({ item, hasScortePanel, onClose, onSwitchToScorte })`:
  - Header con tab switcher: Proposta (attivo) | Planning/Scorte (se detail disponibile) + ✕
  - Strip codice articolo + misura
  - Blocco **Quantità proposta**: `proposal_qty_computed` + misura + `proposal_reason_summary` + `note_fragment`
  - Blocco **Stato export**: `BackendProposalStatusBadge` + nota blocco XLSX se Error
  - Blocco **Logica proposal**: `effective_proposal_logic_key` label/descrizione, fallback badge se diverge da `requested_proposal_logic_key`, `proposal_fallback_reason`
  - Blocco **Diagnostica locale**: `proposal_local_warnings` (lista — solo se non vuota)
  - Footer azioni V1: `Aggiungi al batch export` / `Rimuovi dal batch` → `toast.info` placeholder
- Aggiornato `PannelloPlanningScorte`: aggiunto `onSwitchToProposal?` prop e tab switcher nell'header
- Aggiornato `CenterColumn`: aggiunto `onOpenProposal` prop e CTA "Apri proposta →" in fondo al centro (con `BackendProposalStatusBadge` inline se disponibile)
- Workspace: `onOpenProposal={() => setRightPanel('proposal')}` passato a `CenterColumn`; guard `rightPanel === 'proposal'` aggiunto nel rendering destra; `onSwitchToProposal` passato a `PannelloPlanningScorte`
