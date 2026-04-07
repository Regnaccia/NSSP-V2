# EASY_DESTINAZIONI - Mapping tecnico sorgente -> target sync interno

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-07

## Purpose

Descrivere come l'elenco destinazioni cliente Easy (`POT_DESTDIV`) viene acquisito e allineato nel target sync interno V2 per il primo slice `destinazioni`.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `POT_DESTDIV`
- catalog reference: `docs/integrations/easy/catalog/POT_DESTDIV.json`

## Sync Unit

- entity code: `destinazioni`
- sync unit prevista: `sync.destinazioni`
- target interno V2: `sync_destinazioni`

## Source Identity

Chiave sorgente tecnica usata per identificare univocamente il record:

- `PDES_COD`

Da catalogo:

- tipo: `varchar(6)`
- nullable: `false`
- primary key: `true`

Identificatore business rilevante per la relazione con il cliente:

- `(CLI_COD, NUM_PROGR_CLIENTE)`

Nota:

- `PDES_COD` e la source identity tecnica consigliata per upsert e idempotenza
- `(CLI_COD, NUM_PROGR_CLIENTE)` va comunque mantenuto nel target sync per collegamento e controlli applicativi futuri

## Source Scope

Per il primo slice il perimetro letto e:

- tutti i record disponibili in `POT_DESTDIV`
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
| `PDES_COD` | `codice_destinazione` | `varchar(6)` -> string | source identity tecnica della destinazione |
| `CLI_COD` | `codice_cli` | `varchar(6)` -> string nullable | riferimento al cliente in anagrafica clienti |
| `NUM_PROGR_CLIENTE` | `numero_progressivo_cliente` | `varchar(6)` -> string nullable | identificatore progressivo destinazione nel perimetro del cliente |
| `PDES_IND` | `indirizzo` | `varchar(55)` -> string nullable | indirizzo destinazione |
| `NAZ_COD` | `nazione_codice` | `varchar(25)` -> string nullable | codice nazione destinazione |
| `CITTA` | `citta` | `varchar(60)` -> string nullable | citta destinazione |
| `PROV` | `provincia` | `varchar(2)` -> string nullable | provincia destinazione |
| `PDES_TEL1` | `telefono_1` | `varchar(25)` -> string nullable | primo numero telefonico destinazione |

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi iniziali e finali sui campi stringa
- conversione di stringhe vuote a `NULL` dove coerente con il target interno
- mantenimento dei codici come stringhe senza reinterpretazione business

Non includere:

- deduzione della destinazione "principale"
- classificazioni operative
- arricchimenti Core

## Target Notes

Il target sync interno `sync_destinazioni` e un mirror o target owned dalla sync unit `destinazioni`.

Per il primo slice deve mantenere:

- la source identity tecnica `PDES_COD`
- il collegamento al cliente tramite `CLI_COD`
- l'identificatore progressivo `NUM_PROGR_CLIENTE`
- i campi di recapito selezionati

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

## Dependencies

Dipendenze da altre sync unit:

- dipende da `clienti`

Motivazione:

- `CLI_COD` collega la destinazione al cliente
- l'ordine di sync deve garantire che l'anagrafica clienti esista prima delle destinazioni

## Known Source Limits

- `POT_DESTDIV` ha primary key tecnica `PDES_COD`, ma il legame business con il cliente passa anche da `CLI_COD` e `NUM_PROGR_CLIENTE`
- nel primo slice non vengono ancora considerati campi aggiuntivi come `CAP`, `PDES_RAG1`, `PDES_RAG2`, `PDES_IND2`
- eventuali record con `CLI_COD` nullo o incoerente richiederanno una regola tecnica esplicita nel task di implementazione

## Open Questions

- valutare se includere `CAP` nel target sync iniziale
- valutare se mantenere anche `PDES_RAG1` e `PDES_RAG2` per descrizione completa della destinazione
- definire come trattare eventuali record `POT_DESTDIV` con `CLI_COD` non risolto in `ANACLI`

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/catalog/POT_DESTDIV.json`
