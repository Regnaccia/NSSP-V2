# TASK-V2-047 - Refresh articoli con ordini per set aside

## Status
Todo

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`
- `docs/task/TASK-V2-046-refresh-sequenziale-articoli-giacenza-e-set-aside.md`

## Goal

Correggere il refresh della surface `articoli` in modo che il ricalcolo di `customer_set_aside` avvenga solo dopo l'allineamento dei dati ordine da cui dipende.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`
- `TASK-V2-044`
- `TASK-V2-046`

## Context

Il flusso oggi documentato per il refresh `articoli` e:

1. `sync_articoli`
2. `sync_mag_reale`
3. `rebuild_inventory_positions`
4. `rebuild_customer_set_aside`

Questo flusso e sufficiente per `giacenza`, ma non garantisce l'aggiornamento corretto di `customer_set_aside`, perche quest'ultimo dipende da:

- `sync_righe_ordine_cliente`
- Core `customer_order_lines`

Il Core `customer_order_lines` non richiede un rebuild materializzato, ma legge dal mirror ordini. Quindi il prerequisito operativo reale del rebuild `customer_set_aside` e:

- `sync_righe_ordine_cliente` aggiornato

Senza questo step, il bottone "Aggiorna dati" della schermata `articoli` puo mostrare:

- `inventory_positions` aggiornato
- `customer_set_aside` ricalcolato su ordini stantii

## Scope

### In Scope

- estensione del refresh backend della surface `articoli`
- esecuzione in ordine di:
  - sync `articoli`
  - sync `mag_reale`
  - rebuild `inventory_positions`
  - sync `righe_ordine_cliente`
  - rebuild `customer_set_aside`
- aggiornamento del feedback UI della surface `articoli`
- documentazione aggiornata del nuovo flusso

### Out of Scope

- scheduler automatico
- calcolo `availability`
- UI ordini dedicata
- nuove surface
- modifiche manuali a ordini o set aside

## Constraints

- la UI invia una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- `customer_set_aside` deve continuare a leggere dal Core `customer_order_lines`, non dal mirror grezzo direttamente
- nessuna scrittura verso Easy
- il task deve mantenere separati:
  - `inventory_positions`
  - `customer_set_aside`
  - `commitments`

## Acceptance Criteria

- il refresh della surface `articoli` esegue anche `sync_righe_ordine_cliente` prima del rebuild `customer_set_aside`
- il dettaglio `articoli` mostra `customer_set_aside` coerente con l'ultimo refresh completato
- la risposta backend rende tracciabile anche lo step `righe_ordine_cliente`
- `python -m pytest tests -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale estensione del `SyncRunner` o service equivalente
- eventuale aggiornamento frontend della surface `articoli` se serve per il reload del nuovo step
- eventuali test backend/frontend coerenti col task
- aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/SYSTEM_OVERVIEW.md`
  - `docs/roadmap/STATUS.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e:

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- non introdurre un secondo bottone o trigger dedicato
- mantenere `customer_order_lines` come Core demand-driven, senza rebuild aggiuntivo
- documentare esplicitamente che il prerequisito operativo di `customer_set_aside` e il mirror ordini aggiornato

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
