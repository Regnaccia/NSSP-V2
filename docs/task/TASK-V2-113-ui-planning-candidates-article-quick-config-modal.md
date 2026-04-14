# TASK-V2-113 - UI Planning Candidates article quick config modal

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
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/task/TASK-V2-108-core-planning-candidates-readability-contracts.md`
- `docs/task/TASK-V2-109-ui-planning-candidates-readability-refinement.md`

## Goal

Ridurre il tempo di correzione delle configurazioni articolo aprendo direttamente dalla vista
planning un modal rapido di configurazione.

## Context

Nel planning emergono problemi configurativi che oggi richiedono cambio contesto verso la surface
`articoli`. Per casi come `INVALID_STOCK_CAPACITY` serve un accesso piu rapido alla configurazione
del singolo articolo.

## Scope

- introdurre una quick action, per esempio un pulsante `ingranaggio`, vicino al codice articolo
- aprire un modal rapido di configurazione articolo dalla vista `Planning Candidates`
- il modal deve riusare i contract gia esistenti del dominio `articoli`
- perimetro minimo configurabile nel modal:
  - famiglia articolo
  - `gestione_scorte_attiva`
  - `stock_months`
  - `stock_trigger_months`
  - `capacity_override_qty`

## Out of Scope

- duplicazione della scheda completa `articoli`
- nuove configurazioni non gia presenti nel dominio `articoli`
- creazione di un secondo dominio di configurazione planning-specifico

## Constraints

- il modal deve restare semanticamente allineato alla surface `articoli`
- nessun contratto di configurazione parallelo o semplificato in modo incoerente
- il quick edit deve essere un entry point operativo, non una seconda schermata autonoma

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `No`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `No`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `Si`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Pattern References

- `Pattern 14 - Configurazione articolo: governance nel modello, visibilita in articoli`
- `Pattern 15 - Governance in admin, consumo nelle surface operative`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Se il modal salva configurazioni che impattano il candidate corrente, il task deve dichiarare:

- se viene ricaricata la sola vista planning
- oppure se viene richiamato un refresh semantico piu ampio

## Acceptance Criteria

- la riga planning espone una quick action di configurazione articolo
- il modal consente l'editing del subset configurativo rilevante
- il salvataggio riusa i contract del dominio `articoli`
- l'operatore puo correggere un errore configurativo senza uscire dalla vista planning

## Deliverables

- quick action UI nella tabella planning
- modal di configurazione articolo rapido
- wiring di save e refresh coerente
- verifiche UI mirate

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude sulla UI `Planning Candidates` e sui contract riusati di
`articoli`.

## Implementation Notes

- se opportuno, riusare componenti o form gia esistenti nella surface `articoli`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Aggiunta quick action `⚙` nella riga Planning accanto al codice articolo.
- Implementato modal rapido di configurazione articolo direttamente da `Planning Candidates`.
- Il modal riusa i contract esistenti del dominio `articoli`:
  - `PATCH /produzione/articoli/{codice}/famiglia`
  - `PATCH /produzione/articoli/{codice}/gestione-scorte-override`
  - `PATCH /produzione/articoli/{codice}/stock-policy-override`
  - `GET /produzione/articoli/{codice}` per hydrate/reload dettaglio
- Subset configurabile nel modal:
  - famiglia articolo
  - gestione scorte attiva (override tri-state)
  - stock months (override)
  - stock trigger months (override)
  - capacity override qty
- Dopo salvataggio viene ricaricata la sola vista planning (`loadCandidates`), senza refresh semantico completo.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
