# EASY_CLIENTI - Mapping tecnico sorgente -> target sync interno

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-07

## Purpose

Descrivere come l'anagrafica clienti Easy (`ANACLI`) viene acquisita e allineata nel target sync interno V2 per il primo slice `clienti`.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `ANACLI`
- catalog reference: `docs/integrations/easy/catalog/ANACLI.json`

## Sync Unit

- entity code: `clienti`
- sync unit prevista: `sync.clienti`
- target interno V2: `sync_clienti`

## Source Identity

Chiave sorgente usata per identificare univocamente il record:

- `CLI_COD`

Da catalogo:

- tipo: `varchar(6)`
- nullable: `false`
- primary key: `true`

## Source Scope

Per il primo slice il perimetro letto e:

- tutti i record disponibili in `ANACLI`
- nessun filtro temporale
- nessun filtro per stato

Strategia iniziale coerente con il task:

- `full_scan`

## Alignment Contract

- alignment strategy: `upsert`
- change acquisition strategy: `full_scan`
- delete handling policy: `mark_inactive`

## Field Mapping

| Source Field | Target Field | Type/Format | Notes |
|--------------|--------------|-------------|-------|
| `CLI_COD` | `codice_cli` | `varchar(6)` -> string | source identity del cliente |
| `CLI_RAG1` | `ragione_sociale` | `varchar(55)` -> string | ragione sociale primaria del cliente |
| `CLI_IND` | `indirizzo` | `varchar(55)` -> string nullable | indirizzo cliente come fornito da Easy |
| `NAZ_COD` | `nazione_codice` | `varchar(25)` -> string nullable | codice nazione / nazionalita cliente |
| `PROV` | `provincia` | `varchar(2)` -> string nullable | provincia cliente |
| `CLI_TEL1` | `telefono_1` | `varchar(25)` -> string nullable | primo numero di telefono |
| `CLI_DTMO` | `source_modified_at` | `datetime` -> datetime nullable | data ultima modifica lato sorgente; utile anche come candidato watermark futuro |

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi iniziali e finali sui campi stringa
- conversione di stringhe vuote a `NULL` dove coerente con il target interno
- parsing di `CLI_DTMO` a `datetime`
- mantenimento dei codici come stringhe senza reinterpretazione business

Non includere:

- classificazioni cliente
- arricchimenti Core
- deduzioni operative

## Target Notes

Il target sync interno `sync_clienti` e un mirror o target owned dalla sync unit `clienti`.

Per il primo slice deve contenere almeno i campi selezionati sopra e una semantica vicina alla sorgente Easy.

Non deve:

- diventare modello Core
- essere progettato per la UI finale
- incorporare logiche di business

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

Nota:

- `CLI_DTMO` non sostituisce il freshness anchor della sync unit
- `CLI_DTMO` resta un campo sorgente utile a change acquisition future

## Dependencies

Dipendenze da altre sync unit:

- nessuna

## Known Source Limits

- `CLI_RAG1` copre solo la prima riga della ragione sociale; `CLI_RAG2` esiste ma non entra nel primo slice
- `CLI_DTMO` e disponibile in sorgente, ma nel primo slice non viene ancora usato come watermark operativo
- campi come `CITTA`, `CAP`, `CLI_EMAIL`, `CLI_TEL2` esistono in `ANACLI`, ma non entrano nel perimetro iniziale

## Open Questions

- valutare se introdurre anche `CITTA` e `CAP` nel target sync `clienti` subito dopo il primo slice
- valutare il passaggio futuro da `full_scan` a strategia `watermark` usando `CLI_DTMO`
- valutare se `CLI_RAG2` debba essere concatenato o mantenuto separato nel target sync

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/task/TASK-V2-007-bootstrap-sync-clienti.md`
- `docs/integrations/easy/catalog/ANACLI.json`
