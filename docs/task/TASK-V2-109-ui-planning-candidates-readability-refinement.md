# TASK-V2-109 - UI Planning Candidates readability refinement

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
- `docs/task/TASK-V2-108-core-planning-candidates-readability-contracts.md`

## Goal

Migliorare la leggibilita e l'usabilita finale della tabella `Planning Candidates` prima
dell'apertura del modulo `Production Proposals`.

## Context

Il modulo planning e ormai stabile sul piano semantico, ma la tabella e ancora migliorabile sul
piano operativo:

- misura non abbastanza evidente
- descrizione per-riga non ancora completa
- famiglia non resa come segnale visivo
- motivi poco sintetici
- destinazione richiesta non visibile

## Scope

- introdurre una colonna dedicata `misura`
- usare `full_order_line_description` come descrizione primaria nel ramo
  `by_customer_order_line`
- mostrare `famiglia_label` come badge con palette centralizzata e fallback neutro
- mostrare badge sintetici per i motivi attivi:
  - `Cliente`
  - `Scorta`
- nei casi misti, mostrare entrambi i badge motivi lasciando la riga una sola volta nella scheda
  `customer`
- esporre `requested_destination_display`
- mostrare la colonna data con la semantica gia fissata:
  - `requested_delivery_date` nel ramo per-riga
  - `earliest_customer_delivery_date` nel ramo aggregato

## Out of Scope

- nuove logiche di planning
- modifiche ai filtri orizzonte
- nuove metriche Core
- production proposals

## Constraints

- la palette famiglie deve essere centralizzata, non hardcoded in piu punti della tabella
- la UI non deve ricostruire descrizione o destinazione da campi grezzi se il Core espone gia i
  campi finali
- i casi `stock-only` non devono mostrare data o destinazione inventate

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

- `Pattern 5 - Pattern UIX prima, spec concreta dopo`
- `Pattern 16 - Core unico, segmentazione solo in UI`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- la tabella planning mostra una colonna dedicata `misura`
- il ramo `by_customer_order_line` mostra la descrizione completa
- il ramo `by_article` e `by_customer_order_line` mostrano la destinazione richiesta quando
  disponibile
- `famiglia_label` e resa come badge
- i motivi attivi sono resi come badge sintetici
- i casi misti restano una sola riga nella scheda `customer`

## Deliverables

- tabella `Planning Candidates` raffinata
- mapping UI dei badge famiglia centralizzato
- test/verifiche mirate UI

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude sulla UI `Planning Candidates`.

## Implementation Notes

- il refinement deve privilegiare leggibilita operativa e densita informativa senza aumentare il
  rumore visivo

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Tabella `Planning Candidates` raffinata con nuove colonne operative:
  - `Misura` dedicata (non piu inline nel codice)
  - `Destinazione` da `requested_destination_display`
  - `Data richiesta` con semantica ramo-specifica gia fissata
- Descrizione ramo `by_customer_order_line` aggiornata:
  - usa `full_order_line_description` come primaria
  - fallback a `display_label` quando assente
- Famiglia resa come badge con palette centralizzata:
  - mapping in un solo punto (`FAMILY_BADGE_CLASSES` + hash stabile per label)
  - fallback neutro per famiglie mancanti
- Motivi resi con badge sintetici:
  - `Cliente`
  - `Scorta`
  - casi misti mostrano entrambi i badge nella stessa riga (senza duplicazioni)
- Mantiene il comportamento coerente per casi `stock-only`:
  - nessuna data o destinazione inventata (`solo scorta` / `—`)
- Conservato e integrato ordinamento su `Codice` e `Data richiesta`.

Verifica:
- `npx tsc --noEmit` (frontend) eseguito con esito positivo.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
