# TASK-V2-129 - UI planning need vs release-now visibility

## Status
Todo

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-040.md`
- `docs/task/TASK-V2-128-core-planning-need-vs-release-now-contract.md`

## Goal

Rendere leggibile nella UI `Planning Candidates` la nuova distinzione tra bisogno eventuale e quantita lanciabile ora introdotta dal Core rebase.

## Context

Senza visibilita UI, il nuovo contratto Core resterebbe opaco e gli operatori continuerebbero a leggere il candidate come se ogni bisogno fosse automaticamente lanciabile.

La vista planning deve quindi mostrare in modo immediato:

- il bisogno eventuale
- la quantita lanciabile ora
- lo stato di rilascio

senza trasformarsi in una seconda proposal view.

## Scope

- consumare in UI i nuovi campi Core:
  - `required_qty_eventual`
  - `release_qty_now_max`
  - `release_status`
- introdurre nella tabella planning una rappresentazione leggibile del nuovo split
- aggiungere almeno un filtro UI per `release_status`
- mantenere compatibilita visiva con il ramo `by_customer_order_line`

## Out of Scope

- modifica delle formule Core
- nuove proposal logic
- redesign completo della tabella planning
- rebase quantitativo del ramo per-riga

## Constraints

Regole UI del primo slice:

- il focus del nuovo split e il ramo `by_article`
- il ramo `by_customer_order_line` non deve mostrare dati inventati
- `release_status` deve essere leggibile come badge/sintesi operativa
- la vista deve continuare a mostrare anche i campi attuali gia consolidati

Opzioni UI ammesse:

- nuova colonna `Rilascio ora`
- oppure qty principale + secondaria leggibile

Ma la resa finale deve mostrare almeno:

- `required_qty_eventual`
- `release_qty_now_max`
- `release_status`

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
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 11 - Distinguere stato operativo da quantita`

## Refresh / Sync Behavior

- `La vista riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- la tabella planning rende visibile il nuovo split `need vs release now`
- esiste almeno un filtro UI per `release_status`
- i candidate `by_article` bloccati da capienza risultano leggibili come tali
- il ramo `by_customer_order_line` non mostra valori falsi per i campi non ancora rebasati

## Deliverables

- refinement UI `Planning Candidates`
- test frontend o verifica mirata coerente con il livello del task

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
