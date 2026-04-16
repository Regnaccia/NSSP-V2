# TASK-V2-125 - UI production proposals logic diagnostics

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-036.md`
- `docs/task/TASK-V2-124-core-proposal-logic-diagnostics.md`

## Goal

Rendere visibile nella UI `Production Proposals` la diagnostica locale delle logiche proposal, cosi da capire subito se una riga ha usato la logica richiesta o e ricaduta su fallback a pezzi.

## Context

Oggi la tabella proposal mostra il risultato finale ma non spiega in modo sufficiente:

- quale logica era stata richiesta
- quale logica e stata effettivamente applicata
- perche una logica piu ricca e ricaduta su `proposal_target_pieces_v1`

Questo genera ambiguita operative, soprattutto sui casi `proposal_full_bar_v1`.

## Scope

- mostrare nella UI `Production Proposals`:
  - logica richiesta
  - logica effettiva
  - motivo del fallback quando presente
- integrare il rendering senza trasformare la tabella principale in una schermata di debug
- mantenere chiaro il legame tra `Qtà` e logica effettiva usata

## Out of Scope

- redesign generale della tabella export preview
- nuovi warning canonici
- nuove logiche proposal oltre quelle gia documentate

## Constraints

- la UI deve usare i campi Core/API locali al modulo proposal
- il fallback reason non va mostrato come warning globale
- la quantita deve restare il dato primario, la diagnostica deve fare da spiegazione secondaria

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 09 - Warning canonico separato dal modulo che lo consuma`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand dedicato`

Resta il comportamento corrente della page `Production Proposals`.

## Acceptance Criteria

- la UI mostra la logica effettiva usata per il calcolo della quantita
- quando `requested_proposal_logic_key != effective_proposal_logic_key`, la UI rende esplicito il fallback
- il motivo del fallback e leggibile senza aprire strumenti di debug
- il build frontend resta verde

## Deliverables

- refinement UI della tabella `Production Proposals`
- eventuali badge/testi secondari per fallback reason
- build frontend mirata

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
npm run build
```

Atteso: exit code `0`.

## Implementation Notes

- la forma piu probabile e:
  - sotto `Qtà` resta la logica effettiva
  - requested logic e fallback reason compaiono come testo secondario o badge compatti
- evitare linguaggio troppo tecnico se puo essere tradotto in label leggibili

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

## Implementation Log

### Tipi TS

- `frontend/src/types/api.ts` — `ProposalWorkspaceRowItem` esteso con `requested_proposal_logic_key: string | null`, `effective_proposal_logic_key: string | null`, `proposal_fallback_reason: string | null`.

### UI

- `frontend/src/pages/surfaces/ProductionProposalsPage.tsx`:
  - Aggiunta funzione `fallbackReasonLabel(reason)` che mappa i 5 codici vocabolario in italiano leggibile (`missing_raw_bar_length` → "barra non configurata", ecc.).
  - Nella cella "Qtà" del workspace, quando `requested_proposal_logic_key !== effective_proposal_logic_key`, compare una riga secondaria in arancione con la logica richiesta (es. "↓ Barra intera") e il motivo del fallback sotto (es. "(barra non configurata)"). La quantità finale e la logica effettiva restano il dato primario.

### Verifica

```
npm run build → exit 0
```
