# TASK-V2-048 - Allineamento operativo righe ordine cliente

## Status
Completed

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

### File modificati

- `src/nssp_v2/sync/righe_ordine_cliente/unit.py`
  - `DELETE_HANDLING`: `"no_delete_handling"` → `"delete_absent_keys"`
  - Docstring modulo aggiornata: contratto esplicito DELETE_HANDLING e strategia full_scan + delete_absent_keys
  - Dopo il loop upsert: costruzione `source_keys` (set di tuple `(order_reference, line_reference)`) e iterazione su `existing` per rimuovere con `session.delete` le righe assenti; `meta.rows_deleted` incrementato per ogni rimozione

- `tests/sync/test_sync_righe_ordine_cliente.py`
  - `test_no_delete_handling_riga_sparita_dalla_sorgente` → invertito e rinominato `test_riga_sparita_dalla_sorgente_viene_rimossa`: ora verifica che la riga sparita venga rimossa (`count == 1`, `rows_deleted == 1`)
  - Aggiunti 4 nuovi test sul comportamento delete:
    - `test_riga_rimossa_e_assente_dal_mirror`
    - `test_riga_sparita_e_ricomparsa`
    - `test_sorgente_vuota_rimuove_tutto`
    - `test_rows_deleted_nel_run_metadata`
  - Aggiunti 2 test di propagazione ai fact derivati:
    - `test_riga_rimossa_non_alimenta_customer_set_aside`
    - `test_riga_rimossa_non_alimenta_commitments`
  - Import modello aggiunti a livello modulo (pattern `# noqa: F401`): `CoreCustomerSetAside`, `CoreCommitment`, `SyncProduzioneAttiva`, `SyncArticolo`, `CoreProduzioneOverride` — necessari perché il fixture `session` chiama `Base.metadata.create_all` prima del corpo dei test

### Nessuna migration aggiuntiva

La tabella `sync_righe_ordine_cliente` è già presente. La modifica è solo comportamentale (il delete era prima assente, ora attivo). Nessuna colonna aggiunta o rimossa.

### Strategia implementata

`full_scan + upsert + delete_absent_keys` (DL-ARCH-V2-020):

1. Fetch completo da sorgente → lista `records`
2. Carica `existing` (mirror corrente) come dict keyed su `(order_reference, line_reference)`
3. Loop upsert: INSERT se assente, UPDATE se presente
4. Costruisce `source_keys = {(r.order_reference, r.line_reference) for r in records}`
5. Rimuove da `existing` ogni chiave non in `source_keys` con `session.delete`
6. `meta.rows_deleted` traccia quante righe sono state rimosse

### Caso verificato esplicitamente (Acceptance Criteria §5)

```
sync([riga_1, riga_2])  # mirror: 2 righe
sync([riga_1])          # riga_2 non è in sorgente → session.delete → mirror: 1 riga
rebuild_customer_set_aside() → 1 record (solo riga_1)
rebuild_commitments() → 1 record (solo riga_1)
```

### Test eseguiti

Suite completa: 468/468 passed.
Frontend: `npm run build` — zero errori.

### Assunzioni

- Le righe con `continues_previous_line=True` sono preservate finché la sorgente le include: se `V_TORDCLI` le restituisce, restano nel mirror; se spariscono dalla full scan, vengono rimosse come qualsiasi altra riga.
- Il comportamento è idempotente: più sync successive con la stessa sorgente producono sempre lo stesso mirror.
- `meta.rows_written` conta tutte le righe processate (insert + update), `meta.rows_deleted` conta solo le rimosse. Questo è coerente con il pattern delle altre sync unit.

## Completed At

2026-04-09

## Completed By

Claude Code
