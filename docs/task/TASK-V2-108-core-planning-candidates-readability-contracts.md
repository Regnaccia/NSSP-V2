# TASK-V2-108 - Core Planning Candidates readability contracts

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
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Rendere il contratto Core di `Planning Candidates` abbastanza ricco da supportare il refinement
finale di leggibilita UI senza ricostruzioni ambigue lato frontend.

## Context

Nel ramo `by_customer_order_line` il mirror e il Core ordini hanno gia:

- segmento descrittivo principale
- `description_lines`
- misura
- data richiesta
- riferimenti destinazione

Oggi il Core `Planning Candidates` usa ancora solo il segmento principale della descrizione e non
espone una destinazione richiesta gia pronta per la UI.

## Scope

- introdurre nel ramo `by_customer_order_line`:
  - `full_order_line_description`
  - `requested_destination_display`
- costruire `full_order_line_description` da:
  - `article_description_segment`
  - `description_lines`
- costruire `requested_destination_display` usando il comportamento destinazione gia consolidato:
  - `nickname_destinazione`
  - fallback label default
- estendere il ramo `by_article` con:
  - `requested_destination_display`
- nel ramo `by_article`, valorizzare `requested_destination_display` solo se associabile in modo
  non ambiguo alla richiesta cliente che guida `earliest_customer_delivery_date`
- usare `Multiple` se il mapping non e univoco
- lasciare `null` il campo nei casi `stock-only`

## Out of Scope

- badge UI
- palette famiglie
- layout tabella
- futura semantica `earliest_uncovered_due_date`

## Constraints

- nessuna concatenazione descrittiva deve essere lasciata alla UI
- nessuna destinazione deve essere inventata nei casi `stock-only`
- il comportamento nickname/default deve riusare il pattern gia attivo nel dominio
  `clienti/destinazioni`

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `Si`
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

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- il ramo `by_customer_order_line` espone `full_order_line_description`
- il ramo `by_customer_order_line` espone `requested_destination_display`
- il ramo `by_article` espone `requested_destination_display` solo quando il mapping alla richiesta
  cliente e spiegabile
- i casi `stock-only` mantengono `requested_destination_display = null`

## Deliverables

- read model `Planning Candidates` esteso
- query Core `Planning Candidates` estese
- test mirati sul contratto Core

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude su Core `Planning Candidates`.

## Implementation Notes

- per il display destinazione riusare il comportamento consolidato del Core
  `clienti_destinazioni`, non duplicare euristiche in planning

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Esteso il read model `PlanningCandidateItem` con:
  - `full_order_line_description` (ramo `by_customer_order_line`)
  - `requested_destination_display` (rami `by_customer_order_line` e `by_article`)
- Introdotto nel Core un contesto di leggibilita per righe ordine:
  - aggrega `description_lines` dalle righe `continues_previous_line=True`
  - costruisce `full_order_line_description` (`segmento principale | segmenti aggiuntivi`)
  - risolve `requested_destination_display` con precedenza consolidata:
    - nickname destinazione (`core_destinazione_config`)
    - fallback default (`ragione_sociale` per main, `indirizzo` per destinazione aggiuntiva)
    - fallback tecnico (codice)
- Ramo `by_customer_order_line`:
  - espone `full_order_line_description`
  - espone `requested_destination_display`
- Ramo `by_article`:
  - espone `requested_destination_display` solo quando `customer_shortage_qty > 0`
  - mapping alla richiesta che guida `earliest_customer_delivery_date`
  - se le destinazioni candidate sono multiple sulla stessa earliest date -> `Multiple`
  - `stock-only` mantiene `requested_destination_display = null`
- Aggiunti test mirati su:
  - descrizione completa per riga ordine
  - destinazione richiesta by_customer_order_line
  - destinazione richiesta by_article (univoca / `Multiple` / `stock-only`)

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
