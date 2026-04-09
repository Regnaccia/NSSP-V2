# TASK-V2-043 - Commitments produzione

## Status
Completed

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

## Completion Notes

### File creati/modificati

**Modificati:**
- `src/nssp_v2/core/commitments/queries.py`
  - Aggiunto `_SOURCE_TYPE_PRODUCTION = "production"`
  - Aggiunto `_build_production_commitments(session, computed_at) -> list[CoreCommitment]`
  - `rebuild_commitments` esteso: ora include sia `customer_order` che `production` nello stesso delete-all + re-insert; restituisce il totale combinato

**Creati:**
- `tests/core/test_core_commitments_produzione.py` — 19 test di integrazione

### Nessuna migration

La tabella `core_commitments` esiste già (TASK-V2-042) ed è progettata per multi-source tramite `source_type`. Nessuna nuova tabella necessaria.

### Logica _build_production_commitments

```
SyncProduzioneAttiva (attivo=True)
  OUTER JOIN CoreProduzioneOverride (bucket="active")   — per filtro forza_completata
  INNER JOIN SyncArticolo ON codice_articolo = materiale_partenza_codice  — per CAT_ART1
  WHERE:
    materiale_partenza_codice IS NOT NULL
    materiale_partenza_per_pezzo IS NOT NULL AND > 0
    forza_completata IS NULL OR = False
    quantita_prodotta IS NULL OR ordinata IS NULL OR prodotta < ordinata
    categoria_articolo_1 IS NOT NULL AND != "0"
```

- `article_code` = `materiale_partenza_codice` (il materiale consumato, non l'articolo prodotto)
- `committed_qty` = `materiale_partenza_per_pezzo` (MM_PEZZO)
- `source_reference` = `str(id_dettaglio)`
- `source_type` = `"production"`

### Esclusioni V1 esplicite

| Caso | Motivo esclusione |
|------|-------------------|
| `CAT_ART1 = "0"` | materia prima in mm — stream futuro separato |
| materiale non in `sync_articoli` | CAT_ART1 non verificabile (INNER JOIN) |
| `CAT_ART1 = None` | non classificato — escluso per sicurezza |
| `materiale_partenza_per_pezzo <= 0` | commitment non valido |
| produzione completata (prodotta >= ordinata) | non piu attiva |
| `forza_completata = True` | override interno — chiusa manualmente |
| `attivo = False` | rimossa dal mirror |

### Test eseguiti

19 test in `tests/core/test_core_commitments_produzione.py`:
- source_type = "production" ✓
- source_reference = str(id_dettaglio) ✓
- committed_qty = MM_PEZZO ✓
- article_code = materiale (non articolo prodotto) ✓
- produzione completata per quantita esclusa ✓
- forza_completata=True esclusa ✓
- produzione attiva inclusa ✓
- attivo=False esclusa ✓
- CAT_ART1 = "0" escluso ✓
- materiale non in sync_articoli escluso ✓
- CAT_ART1 != "0" incluso ✓
- CAT_ART1 = None escluso ✓
- materiale_codice None escluso ✓
- materiale_per_pezzo None escluso ✓
- materiale_per_pezzo = 0 escluso ✓
- piu produzioni stesso materiale aggregate ✓
- rebuild include entrambe le provenienze ✓
- aggregazione cross-source stesso articolo ✓
- rebuild deterministico production ✓

Suite completa: 435/435 passed.

### Test non eseguiti

- Test con dati reali Easy: non eseguibili senza connessione.
- Test HTTP: il task non introduce endpoint API.

### Assunzioni

- Il join tra `SyncProduzioneAttiva` e `SyncArticolo` su `materiale_partenza_codice = codice_articolo` usa INNER JOIN: materiali non presenti in `sync_articoli` vengono esclusi (impossibile verificare `CAT_ART1`).
- Il filtro "attiva" replica la logica del Core produzioni (`_build_query_attive` con `stato="attiva"`): le due logiche devono restare coerenti.
- `materiale_partenza_per_pezzo` rappresenta pezzi da prelevare (non mm) quando `CAT_ART1 != "0"`.
- `source_reference = str(id_dettaglio)` permette tracciabilita verso la produzione sorgente senza FK persistita.

### Limiti noti

- Casi `CAT_ART1 = "0"` (materia prima in mm) non gestiti in V1: stream futuro separato (alert scorta materia prima).
- Il filtro "attiva" e duplicato in `_build_production_commitments` rispetto a `_build_query_attive` del Core produzioni: se la logica di stato cambia, entrambi vanno aggiornati.
- Nessun endpoint API esposto.

### Follow-up suggeriti

- Computed fact `availability = inventory - commitments` (DL-ARCH-V2-017 §8).
- Stream `CAT_ART1 = "0"`: alert/controllo scorta materia prima in mm.
- Endpoint `POST /api/core/commitments/rebuild` per trigger manuale.
- Fattorizzare il filtro "attiva" in una funzione condivisa tra Core produzioni e Core commitments.
