# TASK-V2-043 - Commitments produzione

## Status
Todo

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-08

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`

## Goal

Estendere il computed fact `commitments` con la provenienza `production`, usando le produzioni attive
non completate come sorgente canonica di impegno materiale.

## Context

Con `DL-ARCH-V2-017` la V2 prevede tra le provenienze iniziali di `commitments`:

- `production`
- `customer_order`

Per la produzione Easy, il materiale impegnato e espresso tramite:

- `MAT_COD`
- `MM_PEZZO`

ma `MM_PEZZO` cambia semantica in funzione di `CAT_ART1` dell'articolo `MAT_COD`.

Nel perimetro V1 di questo task si adotta una scelta stretta:

- in scope solo produzioni con `MAT_COD.CAT_ART1 != 0`
- quindi solo casi in cui `MM_PEZZO` rappresenta il numero di pezzi da prelevare dal magazzino

Fuori scope per ora:

- `MAT_COD.CAT_ART1 = 0`
- cioe la materia prima espressa in millimetri

Questa parte potra diventare in futuro uno stream separato di controllo scorte / alert su materia prima.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-030`
- `TASK-V2-042`

## Scope

### In Scope

- estensione del modello Core `commitments` alla provenienza `source_type = production`
- input dal Core `produzioni`
- considerazione delle sole produzioni:
  - `bucket = active`
  - non `completate`
- lookup di `MAT_COD -> CAT_ART1` tramite anagrafica articoli
- inclusione dei soli casi con `CAT_ART1 != 0`
- calcolo V1:
  - `committed_qty = MM_PEZZO`
- query/read model aggregato almeno per `article_code`

### Out of Scope

- casi con `CAT_ART1 = 0`
- impegni materia prima in millimetri
- availability
- allocazioni
- UI dedicata commitments
- politiche di sospensione accumuli o alert scorta minima

## Constraints

- il task deve leggere dal Core `produzioni`, non dai mirror sync grezzi
- `MM_PEZZO` non va interpretato senza il lookup su `CAT_ART1`
- i casi `CAT_ART1 = 0` devono essere esplicitamente esclusi dal V1
- il modello deve restare compatibile con future provenienze aggiuntive e con futuri impegni materia prima

## Acceptance Criteria

- esiste la provenienza `production` nel computed fact `commitments`
- vengono considerate solo produzioni attive e non completate
- vengono inclusi solo materiali con `CAT_ART1 != 0`
- `committed_qty` viene calcolata come `MM_PEZZO`
- esiste almeno una query/read model aggregata per `article_code`
- `python -m pytest tests -q` passa

## Deliverables

- estensione modelli Core `commitments`
- query/read models minimi
- test backend minimi su:
  - filtro `bucket/state`
  - lookup `MAT_COD -> CAT_ART1`
  - esclusione `CAT_ART1 = 0`
  - `committed_qty = MM_PEZZO`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del computed fact `commitments` per provenienza `production`.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- computed fact/read models introdotti o estesi
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- mantenere il perimetro V1 stretto e solo su `CAT_ART1 != 0`
- trattare la materia prima `CAT_ART1 = 0` come stream futuro separato
- mantenere `source_type = production` coerente con la stessa fact `commitments`
- non introdurre ancora `availability`
