# EASY_ARTICOLI - Mapping tecnico sorgente -> target sync interno

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-07

## Purpose

Descrivere come l'anagrafica articoli Easy (`ANAART`) viene acquisita e allineata nel target sync interno V2 per il primo slice `articoli`.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `ANAART`
- catalog reference: `docs/integrations/easy/catalog/ANAART.json`

## Sync Unit

- entity code: `articoli`
- sync unit prevista: `sync.articoli`
- target interno V2: `sync_articoli`

## Source Identity

Chiave sorgente usata per identificare univocamente il record:

- `ART_COD`

Da catalogo:

- tipo: `varchar(25)`
- nullable: `false`
- primary key: `true`

## Source Scope

Per il primo slice il perimetro letto e:

- tutti i record disponibili in `ANAART`
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
| `ART_COD` | `codice_articolo` | `varchar(25)` -> string | source identity dell'articolo |
| `ART_DES1` | `descrizione_1` | `varchar(100)` -> string nullable | descrizione articolo riga 1 |
| `ART_DES2` | `descrizione_2` | `varchar(100)` -> string nullable | descrizione articolo riga 2 |
| `UM_COD` | `unita_misura_codice` | `varchar(3)` -> string nullable | unita di misura articolo |
| `ART_DTMO` | `source_modified_at` | `datetime` -> datetime nullable | data ultima modifica lato sorgente; utile anche come candidato watermark futuro |
| `CAT_ART1` | `categoria_articolo_1` | `varchar(6)` -> string nullable | categoria articolo primaria |
| `MAT_COD` | `materiale_grezzo_codice` | `varchar(25)` -> string nullable | codice materiale grezzo associato alla produzione |
| `REGN_QT_OCCORR` | `quantita_materiale_grezzo_occorrente` | `numeric(18,5)` -> decimal nullable | quantita materiale grezzo occorrente per produzione |
| `REGN_QT_SCARTO` | `quantita_materiale_grezzo_scarto` | `numeric(18,5)` -> decimal nullable | quantita di scarto materiale grezzo per produzione |
| `ART_MISURA` | `misura_articolo` | `varchar(20)` -> string nullable | misura articolo come fornita da Easy |
| `COD_IMM` | `codice_immagine` | `varchar(3)` -> string nullable | riferimento immagine articolo |
| `ART_CONTEN` | `contenitori_magazzino` | `varchar(15)` -> string nullable | contenitori dedicati in magazzino |
| `ART_KG` | `peso_grammi` | `numeric(18,5)` -> decimal nullable | peso articolo; nel primo slice trattato come grammi secondo convenzione operativa corrente, da validare rispetto al naming sorgente |

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi iniziali e finali sui campi stringa
- conversione di stringhe vuote a `NULL` dove coerente con il target interno
- parsing di `ART_DTMO` a `datetime`
- mantenimento dei codici come stringhe senza reinterpretazione business
- mantenimento dei valori numerici come decimal senza arrotondamenti business

Non includere:

- classificazioni operative di produzione
- deduzioni di magazzino
- regole Core sulla configurazione articolo

## Target Notes

Il target sync interno `sync_articoli` e un mirror o target owned dalla sync unit `articoli`.

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

- `ART_DTMO` non sostituisce il freshness anchor della sync unit
- `ART_DTMO` resta un campo sorgente utile a change acquisition future

## Dependencies

Dipendenze da altre sync unit:

- nessuna

## Known Source Limits

- `ART_DES1` e `ART_DES2` restano separati nel primo slice; la composizione per display verra decisa nel Core
- `ART_DTMO` e disponibile in sorgente, ma nel primo slice non viene ancora usato come watermark operativo
- il significato operativo di `ART_KG` va confermato rispetto al naming sorgente; nel primo slice e trattato secondo la convenzione corrente indicata dal dominio
- campi ulteriori presenti in `ANAART` non entrano nel perimetro iniziale finche non saranno richiesti da sync/Core/UI

## Open Questions

- valutare se esporre nel Core un `display_label` composto da `ART_DES1` + `ART_DES2`
- valutare il passaggio futuro da `full_scan` a strategia `watermark` usando `ART_DTMO`
- validare in modo definitivo l'unita di misura operativa del campo `ART_KG`
- valutare se `MAT_COD` debba diventare una futura dipendenza esplicita verso una sync materiali/articoli base

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/catalog/ANAART.json`
