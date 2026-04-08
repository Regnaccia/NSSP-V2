# TASK-V2-042 - Commitments cliente

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
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`

## Goal

Costruire il primo computed fact `commitments` da provenienza `customer_order`, a partire dal Core
`customer_order_lines`, come base riusabile per i futuri calcoli di `availability`.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`

## Context

Con `DL-ARCH-V2-017` la V2 ha introdotto `commitments` come computed fact canonico del Core.

Per la provenienza `customer_order`, il building block corretto non e il mirror sync grezzo ma:

- `customer_order_lines`

Il primo slice V1 dei commitments cliente deve quindi:

- leggere le righe ordine canoniche dal Core
- produrre una fact uniforme `commitments`
- usare come quantita impegnata la quota ancora davvero da coprire operativamente

Nel perimetro V1:

- `committed_qty = open_qty`

dove `open_qty` arriva gia dal Core ordini e tiene conto di:

- ordinato
- evaso
- quantita gia inscatolata/appartata

## Scope

### In Scope

- modello Core `commitments` o equivalente
- provenienza iniziale `source_type = customer_order`
- calcolo `committed_qty` da `customer_order_lines.open_qty`
- campi canonici minimi:
  - `article_code`
  - `source_type`
  - `source_reference`
  - `committed_qty`
  - `computed_at`
- read model/query di aggregazione almeno per `article_code`
- esclusione delle righe con `open_qty <= 0`

### Out of Scope

- commitments da `production`
- disponibilita finale
- allocazioni
- priorita
- compensazioni tra sorgenti
- UI dedicata commitments

## Constraints

- il task deve leggere dal Core ordini, non dal mirror `sync_righe_ordine_cliente`
- `committed_qty` cliente V1 deve coincidere con `open_qty`
- gli stati `set_aside_qty` e `fulfilled_qty` restano visibili a monte nel Core ordini, ma non devono generare doppio conteggio
- il modello deve restare compatibile con future provenienze aggiuntive

## Acceptance Criteria

- esiste un computed fact `commitments` per `source_type = customer_order`
- `committed_qty` viene calcolata usando `open_qty`
- le righe con `open_qty <= 0` non generano commitments attivi
- esiste almeno una query/read model aggregata per `article_code`
- `python -m pytest tests -q` passa

## Deliverables

- modelli Core `commitments`
- eventuale migration necessaria
- query/read models minimi
- test backend minimi su:
  - mapping da `customer_order_lines`
  - esclusione righe chiuse
  - aggregazione per articolo
  - `committed_qty = open_qty`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del computed fact `commitments`.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- computed fact/read models introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- mantenere il perimetro V1 stretto: solo `customer_order`
- non introdurre ancora `availability`
- non anticipare deduzioni avanzate oltre `committed_qty = open_qty`
- lasciare `source_reference` abbastanza ricco da risalire alla riga ordine canonica
