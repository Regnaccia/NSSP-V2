# EASY_RIGHE_ORDINE_CLIENTE - Mapping tecnico sorgente -> target sync interno

## Status
Draft

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-08

## Purpose

Descrivere in modo tecnico e operativo come la vista Easy `V_TORDCLI` viene acquisita e allineata
nel target sync interno V2 come primo mirror delle righe ordine cliente.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `V_TORDCLI`
- base dataset: righe ordine cliente esposte direttamente dalla vista, senza testata ordine separata

## Sync Unit

- entity code: `righe_ordine_cliente`
- sync unit prevista: `RigheOrdineClienteSyncUnit`
- target interno V2: `sync_righe_ordine_cliente`

## Source Identity

Chiave sorgente proposta per identificare univocamente la riga:

- `(DOC_NUM, NUM_PROGR)`

Note:

- `DOC_NUM` identifica l'ordine interno Easy
- `NUM_PROGR` identifica la riga ordine
- la vista non dichiara primary key tecniche nel catalogo JSON, quindi questa chiave e assunta come identita tecnica V1

## Source Scope

Perimetro letto dalla sorgente:

- tutte le righe ordine cliente esposte da `V_TORDCLI`
- incluse righe descrittive di continuazione con `COLL_RIGA_PREC = true`

Esclusioni note:

- nessuna al livello sync V1

## Alignment Contract

- alignment strategy: `upsert`
- change acquisition strategy: `full_scan`
- delete handling policy: `no_delete_handling`

Note:

- la strategia e `Draft` e andrà confermata quando sarà chiaro il comportamento storico della vista
- il primo slice punta a preservare il dataset, non a introdurre ancora lifecycle avanzato degli ordini

## Field Mapping

| Source Field | Target Field | Type/Format | Notes |
|--------------|--------------|-------------|-------|
| `DOC_NUM` | `order_reference` | `string` | numero ordine interno Easy |
| `NUM_PROGR` | `line_reference` | `integer/string` | numero progressivo riga ordine |
| `DOC_DATA` | `order_date` | `datetime` | data ordine |
| `DOC_PREV` | `expected_delivery_date` | `datetime` | data prevista evasione |
| `CLI_COD` | `customer_code` | `string` | codice cliente |
| `PDES_COD` | `destination_code` | `string` | codice destinazione |
| `NUM_PROGR_CLIENTE` | `customer_destination_progressive` | `string` | se vuoto indica destinazione principale |
| `N_ORDCLI` | `customer_order_reference` | `string` | riferimento ordine cliente |
| `ART_COD` | `article_code` | `string` | puo essere vuoto sulle righe di continuazione descrittiva |
| `ART_DESCR` | `article_description_segment` | `string` | segmento descrittivo della riga |
| `ART_MISURA` | `article_measure` | `string` | misura articolo |
| `DOC_QTOR` | `ordered_qty` | `numeric` | quantita ordinata |
| `DOC_QTEV` | `fulfilled_qty` | `numeric` | quantita gia evasa |
| `DOC_QTAP` | `set_aside_qty` | `numeric` | quantita gia inscatolata/appartata per cliente; non ancora evasa e non ancora uscita dai movimenti di magazzino |
| `DOC_PZ_NETTO` | `net_unit_price` | `numeric` | prezzo unitario gia scontato |
| `COLL_RIGA_PREC` | `continues_previous_line` | `boolean` | `true` se la riga estende descrittivamente la riga precedente |

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi su campi stringa
- uppercase tecnico per codici rilevanti dove necessario
- cast coerente di valori numerici e date
- conversione `NULL` coerente col target interno
- normalizzazione di stringhe vuote a `NULL` dove appropriato

Non consentito nel layer sync:

- concatenare o fondere righe descrittive
- derivare `open_qty`
- calcolare `commitments`
- interpretare business logic finale da `DOC_QTAP`

## Target Notes

Il target sync interno deve preservare la granularita sorgente:

- una riga sync per ogni riga della vista `V_TORDCLI`
- le righe con `COLL_RIGA_PREC = true` vanno conservate come record separati
- nessuna fusione descrittiva nel mirror sync

Questo consente al Core di decidere a valle come aggregare le descrizioni in una struttura tipo:

- `description_lines`

senza perdere la forma originale della sorgente.

Il target sync deve anche preservare `DOC_QTAP` come dato sorgente distinto, perche rappresenta
una quota gia fisicamente non libera per il cliente pur non essendo ancora registrata come uscita
nei movimenti di magazzino.

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

Dipendenze previste:

- nessuna strettamente tecnica nel layer sync V1

Dipendenze logiche future nel Core:

- possibile riuso di `clienti`
- possibile riuso di `destinazioni`
- possibile riuso di `articoli`

## Known Source Limits

- `V_TORDCLI` non dichiara primary key nel catalogo JSON
- la vista mescola dati di testata ordine e dati di riga nello stesso dataset
- esistono righe di continuazione descrittiva con `COLL_RIGA_PREC = true`
- le righe di continuazione possono avere `ART_COD` vuoto
- `DOC_QTAP` rappresenta una quota gia inscatolata/appartata per cliente: non e ancora evasione, ma non e piu giacenza libera

## Open Questions

- confermare che `(DOC_NUM, NUM_PROGR)` sia sempre stabile e univoca come source identity
- chiarire il ruolo preciso di `DOC_QTAP` nella futura distinzione tra `commitments`, `set_aside stock` e `availability`
- chiarire se la vista contenga solo righe aperte o anche storico ordini chiusi
- chiarire se serva in futuro una seconda sorgente Easy per una testata ordine piu esplicita

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
