# TASK-V2-048 - Allineamento operativo righe ordine cliente

## Status
Todo

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-020.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`

## Goal

Correggere `sync_righe_ordine_cliente` affinche rappresenti solo le righe attive presenti in `V_TORDCLI`, rimuovendo dal mirror operativo le righe non piu in sorgente.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`
- `TASK-V2-042`
- `TASK-V2-044`

## Context

La sync ordini cliente e nata con:

- `full_scan + upsert + no_delete_handling`

Questo comporta che una riga:

- presente ieri in `V_TORDCLI`
- sparita oggi per emissione DDT o chiusura operativa

resta nel mirror e continua ad alimentare:

- `customer_order_lines`
- `commitments`
- `customer_set_aside`

Per questa sorgente il mirror corretto e operativo, non storico.

## Scope

### In Scope

- cambiare la sync `righe_ordine_cliente` da mirror conservativo a mirror operativo attivo
- introdurre un delete handling che rimuova dal mirror le righe assenti nella full scan corrente
- aggiornare test e documentazione della sync ordini
- verificare che i fact downstream non mantengano piu righe sparite:
  - `customer_order_lines`
  - `commitments`
  - `customer_set_aside`

### Out of Scope

- introduzione dello storico ordini Easy
- nuove surface UI ordini
- availability
- audit locale sugli ordini chiusi

## Constraints

- Easy resta strettamente `read-only`
- la source identity `(DOC_NUM, NUM_PROGR)` resta invariata
- le righe con `COLL_RIGA_PREC = true` continuano a essere preservate finche presenti in sorgente
- la correzione deve mantenere idempotenza e run metadata coerenti
- il mirror va trattato come dataset attivo corrente, non come archivio

## Acceptance Criteria

- le righe non piu presenti in `V_TORDCLI` vengono rimosse da `sync_righe_ordine_cliente`
- `customer_order_lines` non include piu righe sparite dalla sorgente
- `commitments` e `customer_set_aside` non vengono piu alimentati da righe chiuse/scomparse
- `python -m pytest tests -q` passa
- viene riportata almeno una verifica esplicita del caso:
  - riga presente al primo sync
  - riga assente al sync successivo
  - record rimosso dal mirror e assente dai fact derivati

## Deliverables

- aggiornamento della sync unit `righe_ordine_cliente`
- eventuale migration solo se davvero necessaria
- test backend aggiornati o estesi
- aggiornamento documentazione tecnica e task correlati

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del caso di riga scomparsa dalla sorgente.

## Implementation Notes

Direzione raccomandata:

- mantenere `full_scan`
- applicare delete handling sul mirror operativo
- evitare soluzioni ibride tipo "tenere tutto ma filtrare dopo"
- lasciare lo storico a un futuro stream separato, non a questo mirror

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
