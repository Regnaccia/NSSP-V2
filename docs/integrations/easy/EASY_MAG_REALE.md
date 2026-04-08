# EASY_MAG_REALE - Mapping tecnico sorgente -> target sync interno

## Status
Draft

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-08

## Purpose

Descrivere come i movimenti di magazzino letti da `MAG_REALE` vengono acquisiti e allineati nel target sync interno V2.

Questo e il primo caso in cui la natura della sorgente suggerisce esplicitamente:

- sync incrementale
- strategia `append_only`
- rebuild completo pianificato a intervalli noti

Questa sorgente e anche il punto di partenza previsto per introdurre, in un successivo slice Core,
il concetto di `giacenza articoli`.

## Source System

- sorgente: `Easy`
- access mode: `read-only`
- tabella o vista sorgente: `MAG_REALE`
- catalog reference: `docs/integrations/easy/catalog/MAG_REALE.json`

## Sync Unit

- entity code previsto: `mag_reale`
- sync unit prevista: `sync.mag_reale`
- target interno V2 previsto: `sync_mag_reale`

## Source Identity

Chiave sorgente usata per identificare univocamente il movimento:

- `ID_MAGREALE`

Nota:

- nel catalogo `MAG_REALE` risulta gia dichiarata come primary key

## Source Scope

Per il primo slice il perimetro letto previsto e:

- tutti i movimenti presenti in `MAG_REALE`
- nessun filtro temporale nel primo bootstrap

Direzione operativa prevista:

- bootstrap iniziale completo
- sync incrementale sui nuovi movimenti
- rebuild completo a intervalli noti, da introdurre con il futuro scheduler

## Alignment Contract

- alignment strategy: `append_only`
- change acquisition strategy: `cursor`
- delete handling policy: `no_delete_handling`

Nota:

- la direzione iniziale assume che Easy registri nuovi movimenti senza modificare i record esistenti
- il dettaglio del cursor/watermark verra fissato nel task tecnico

## Field Mapping

Campi rilevanti fissati per il primo slice:

| Source Field | Target Field | Type/Format | Notes |
|--------------|--------------|-------------|-------|
| `ID_MAGREALE` | `id_movimento` | `numeric(10,0)` -> integer | identita tecnica del movimento |
| `ART_COD` | `codice_articolo` | `varchar(25)` -> string nullable | codice articolo |
| `QTA_CAR` | `quantita_caricata` | `numeric(18,6)` -> decimal nullable | quantita caricata a magazzino |
| `QTA_SCA` | `quantita_scaricata` | `numeric(18,6)` -> decimal nullable | quantita scaricata a magazzino |
| `CAUM_COD` | `causale_movimento_codice` | `varchar(6)` -> string nullable | causale movimento |
| `DOC_DATA` | `data_movimento` | `datetime` -> datetime nullable | data movimento |

## Cross-Source Normalization Note

Nota tecnica importante per il primo slice:

- alcuni valori di `ART_COD` in `MAG_REALE` risultano formattati male
- per mitigare il problema, il confronto con l'anagrafica articoli deve usare una normalizzazione tecnica coerente

Regola iniziale di normalizzazione del codice articolo:

- trim spazi iniziali e finali
- rimozione degli spazi interni non significativi, se gia adottata nel codice applicativo
- conversione a maiuscolo

Regola di confronto cross-source:

> Il collegamento tecnico tra `MAG_REALE.ART_COD` e `ANAART.ART_COD` deve avvenire su codice normalizzato in maiuscolo.

Questa normalizzazione resta tecnica:

- non modifica il significato business del codice
- non autorizza correzioni manuali del valore sorgente in Easy

## Deferred Fields

Campi presenti in sorgente ma rinviati a una fase successiva o da chiarire semanticamente:

- `DEP_COD`
- `ART_DES1`
- `FLG_ANA`
- `COD_ANA`
- `VAL_UNIT`
- `VAL_TOT`
- `MAG_DTREG`
- `DOC_NUM`
- altri campi non ancora rilevanti per il primo slice

## Technical Normalization Allowed

Trasformazioni tecniche consentite nel layer sync:

- trim spazi iniziali e finali sui campi stringa
- normalizzazione tecnica di `ART_COD` per confronto cross-source:
  - uppercase
  - rimozione spazi non significativi dove necessario
- conversione di stringhe vuote a `NULL` dove coerente con il target interno
- parsing dei campi numerici a `Decimal`
- parsing dei campi data a `datetime`

Non includere:

- calcolo giacenze
- deduzioni di stock disponibile
- aggregazioni Core
- interpretazioni operative delle causali

## Target Notes

Il target sync interno previsto e un mirror append-only dei movimenti di magazzino.

Scelte attese nel task tecnico:

- strategia tecnica del cursor incrementale
- politica di deduplicazione su `ID_MAGREALE`
- modalita di rebuild completo quando verra introdotto lo scheduler

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

Dipendenze iniziali:

- nessuna dipendenza bloccante per il mirror tecnico

Dipendenze Core potenziali future:

- `articoli`
- futuro slice `giacenza articoli`

## Known Source Limits

- la strategia incrementale dipende dall'assunzione che Easy aggiunga movimenti senza modificarli
- il rebuild completo sara necessario per compensare eventuali anomalie di sorgente o derive nel tempo
- l'interpretazione business delle causali resta fuori dal layer sync
- alcuni valori di `ART_COD` possono risultare malformattati o incoerenti come casing/spaziatura rispetto a `ANAART`

## Open Questions

- quale campo o combinazione usare come cursor incrementale operativo
- se `ID_MAGREALE` basta da solo come ordinamento incrementale affidabile
- come fissare il rebuild completo periodico nel futuro scheduler
- fino a che punto la normalizzazione di `ART_COD` puo spingersi senza introdurre collisioni

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/catalog/MAG_REALE.json`
