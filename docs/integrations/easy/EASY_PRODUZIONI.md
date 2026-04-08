# EASY_PRODUZIONI - Mapping tecnico sorgente -> target sync interno

## Status
Draft

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-08

## Purpose

Descrivere come le produzioni Easy vengono lette e allineate nel target sync interno V2 per il primo slice `produzioni`.

Nel perimetro attuale la documentazione copre due sorgenti quasi equivalenti:

- `DPRE_PROD` per produzioni attive
- `SDPRE_PROD` per produzioni storiche

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabelle o viste sorgente:
  - `DPRE_PROD`
  - `SDPRE_PROD`
- catalog reference:
  - `docs/integrations/easy/catalog/DPRE_PROD.json`
  - `docs/integrations/easy/catalog/SDPRE_PROD.json`

## Sync Unit

- entity code logica: `produzioni`
- sync unit previste:
  - `sync.produzioni_attive`
  - `sync.produzioni_storiche`
- target interni V2 previsti:
  - `sync_produzioni_attive`
  - `sync_produzioni_storiche`

## Structural Check

Esito del confronto tecnico iniziale:

- `DPRE_PROD` e `SDPRE_PROD` hanno struttura logicamente equivalente
- entrambe espongono `31` colonne
- l'ordine e la semantica generale risultano allineati

Differenze tecniche osservate nel catalogo:

- `COD_RIGA`
  - `DPRE_PROD`: `varchar(25)`
  - `SDPRE_PROD`: `varchar(6)`
- `SCRITTO` vs `scritto`
  - differenza di casing del nome colonna

Regola documentale iniziale:

> Le due sorgenti vengono trattate come la stessa entita logica `produzioni`, salvo futura evidenza contraria.

## Source Identity

Chiave sorgente da confermare nel task tecnico.

Candidate iniziali:

- `ID_DETTAGLIO`

Nota:

- nel catalogo non risultano primary key dichiarate
- `ID_DETTAGLIO` e il candidato piu forte per identita tecnica nel primo slice

## Source Scope

Per il primo slice il perimetro letto previsto e:

- tutte le righe disponibili in `DPRE_PROD`
- tutte le righe disponibili in `SDPRE_PROD`
- nessun filtro temporale nel primo bootstrap

Regola adottata:

- `DPRE_PROD` alimenta un target mirror dedicato per le produzioni attive
- `SDPRE_PROD` alimenta un target mirror dedicato per le produzioni storiche
- l'aggregazione `attive + storiche` non avviene nel layer `sync`, ma nel `core`

## Alignment Contract

Direzione iniziale consigliata:

- alignment strategy: `upsert`
- change acquisition strategy: `full_scan`
- delete handling policy: da definire

Nota:

- il contratto runtime puo evolvere in modo indipendente per `attive` e `storiche`
- la distinzione tra `active` e `historical` va preservata nel layer `sync`

## Field Mapping

Campi rilevanti fissati per il primo slice:

| Source Field | Target Field | Type/Format | Notes |
|--------------|--------------|-------------|-------|
| `CLI_RAG1` | `cliente_ragione_sociale` | `varchar(55)` -> string nullable | cliente destinatario della produzione |
| `ART_COD` | `codice_articolo` | `varchar(25)` -> string nullable | codice articolo |
| `ART_DESCR` | `descrizione_articolo` | `varchar(100)` -> string nullable | descrizione articolo principale |
| `ART_DES2` | `descrizione_articolo_2` | `varchar(150)` -> string nullable | seconda descrizione articolo |
| `NR_RIGA` | `numero_riga_documento` | `numeric(10,0)` -> integer/decimal nullable | numero riga documento |
| `DOC_QTOR` | `quantita_ordinata` | `numeric(18,5)` -> decimal nullable | quantita ordinata |
| `DOC_QTEV` | `quantita_prodotta` | `numeric(18,5)` -> decimal nullable | quantita prodotta |
| `MAT_COD` | `materiale_partenza_codice` | `varchar(25)` -> string nullable | materiale di partenza |
| `MM_PEZZO` | `materiale_partenza_per_pezzo` | `numeric(18,5)` -> decimal nullable | materiale di partenza necessario per un pezzo |
| `ART_MISURA` | `misura_articolo` | `varchar(20)` -> string nullable | misura articolo |
| `DOC_NUM` | `numero_documento` | `varchar(10)` -> string nullable | numero documento |
| `COD_IMM` | `codice_immagine` | `varchar(1)` -> string nullable | riferimento immagine articolo |
| `NUM_ORDINE` | `riferimento_numero_ordine_cliente` | `varchar(10)` -> string nullable | riferimento ordine cliente |
| `RIGA_ORDINE` | `riferimento_riga_ordine_cliente` | `numeric(18,0)` -> integer/decimal nullable | riferimento riga ordine cliente |
| `NOTE_ARTICOLO` | `note_articolo` | `varchar(55)` -> string nullable | note articolo |

## Deferred Fields

Campi presenti in sorgente ma rinviati a una fase successiva o da chiarire semanticamente:

- `CLI_COD`
- `NUM_PROGR`
- `QTA_DAPR`
- `QTA_ORAPR`
- `DATA_PROD`
- `QTA_NEC`
- `QTA_DISP`
- `QTA_MANC`
- `MP_DAUSARE`
- `DOC_EVAS`
- `STAMPATO`
- `COD_RIGA`
- `DOC_RIGA`
- `SCRITTO` / `scritto`
- `CAT_ART6`

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi iniziali e finali sui campi stringa
- conversione di stringhe vuote a `NULL` dove coerente con il target interno
- parsing dei campi numerici a `Decimal`
- normalizzazione tecnica del casing del nome colonna `SCRITTO`/`scritto`
- gestione tecnica della differenza di ampiezza su `COD_RIGA` senza reinterpretazione business

Non includere:

- join o deduzioni Core
- logiche di pianificazione
- classificazioni operative di produzione

## Target Notes

Il target sync interno per `produzioni` e definito come doppio mirror separato.

Scelte adottate:

- `sync_produzioni_attive` per `DPRE_PROD`
- `sync_produzioni_storiche` per `SDPRE_PROD`
- nessun campo `source_bucket` nel mirror sync
- eventuale `bucket = active | historical` introdotto solo nel `core`

## Run Metadata Expectations

Metadati minimi attesi per la sync unit:

- `run_id`
- `started_at`
- `finished_at`
- `status`
- `rows_seen`
- `rows_written`
- `rows_deleted` se applicabile
- `error_message` se fallita

## Freshness Anchor

Valore minimo usato per valutare la freshness:

- `last_success_at`

## Dependencies

Dipendenze potenziali da valutare:

- `articoli`
- eventualmente `clienti`

Nel primo draft restano non ancora fissate.

## Known Source Limits

- nessuna primary key dichiarata nel catalogo
- `DPRE_PROD` e `SDPRE_PROD` sono molto simili ma non perfettamente identiche
- la semantica esatta di alcune quantita va validata prima della sync reale

## Open Questions

- usare `ID_DETTAGLIO` come identita tecnica definitiva
- decidere se i campi quantita rinviati debbano entrare gia nel primo slice

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/integrations/easy/catalog/DPRE_PROD.json`
- `docs/integrations/easy/catalog/SDPRE_PROD.json`
