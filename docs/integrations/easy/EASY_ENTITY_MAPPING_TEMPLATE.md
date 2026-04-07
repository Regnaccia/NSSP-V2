# EASY_<ENTITY> - Mapping tecnico sorgente -> target sync interno

## Status
Draft

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
YYYY-MM-DD

## Purpose

Descrivere in modo tecnico e operativo come una entita letta da Easy viene acquisita e allineata nel target sync interno V2.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `...`
- eventuale query/base dataset: `...`

## Sync Unit

- entity code: `...`
- sync unit prevista: `...`
- target interno V2: `...`

## Source Identity

Chiave sorgente usata per identificare univocamente il record.

Esempio:

- `CLI_COD`
- `(CLI_COD, NUM_PROGR_CLIENTE)`

## Source Scope

Descrivere il perimetro letto dalla sorgente.

Esempi:

- tutti i record attivi
- tutti i record senza filtro temporale
- record filtrati per stato

Se esistono esclusioni note, indicarle esplicitamente.

## Alignment Contract

- alignment strategy: `full_replace` | `upsert` | `upsert_with_delete_reconciliation` | `append_only`
- change acquisition strategy: `full_scan` | `watermark` | `cursor` | `external_change_token`
- delete handling policy: `hard_delete` | `soft_delete` | `mark_inactive` | `no_delete_handling`

## Field Mapping

| Source Field | Target Field | Type/Format | Notes |
|--------------|--------------|-------------|-------|
| `SOURCE_COL` | `target_col` | `string` | note tecniche |

## Technical Normalization Allowed

Elencare solo trasformazioni tecniche consentite nel layer sync.

Esempi:

- trim spazi
- uppercase o lowercase tecnico
- cast tipi
- conversione `NULL` coerente con il target interno
- parsing date

Non includere:

- logiche di business
- arricchimenti Core
- deduzioni operative

## Target Notes

Descrivere brevemente il target sync interno.

Esempi:

- tabella mirror interna
- staging owned dalla sync unit
- vincoli tecnici attesi

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

Indicare dipendenze da altre sync unit, se esistono.

Esempi:

- nessuna
- dipende da `clienti`
- dipende da `articoli`

## Known Source Limits

Documentare eventuali limiti della sorgente Easy.

Esempi:

- campi non affidabili
- codifiche legacy
- assenza di timestamp modifica
- delete non osservabile direttamente

## Open Questions

- punto aperto 1
- punto aperto 2

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
