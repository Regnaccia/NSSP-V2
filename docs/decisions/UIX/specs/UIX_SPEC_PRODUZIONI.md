# UIX_SPEC_PRODUZIONI - Variante a 2 colonne

## Status
Draft

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-08

## Purpose

Documentare come il pattern UIX multi-colonna standard viene applicato al caso `produzioni`.

## Related Documents

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`
- `docs/task/TASK-V2-028-sync-produzioni-attive.md`
- `docs/task/TASK-V2-029-sync-produzioni-storiche.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`

## Variant

- pattern adottato: `2 colonne`

## Column Model

### Colonna 1 - Lista produzioni

Contiene:

- elenco produzioni aggregate dal `core`
- selezione singola produzione
- indicatori sintetici di:
  - cliente destinatario
  - articolo
  - numero documento / riga
  - bucket
  - stato produzione

Requisiti UX minimi:

- lista scrollabile in modo indipendente
- selezione attiva sempre evidente
- leggibilita orientata a scansione rapida

### Colonna 2 - Dettaglio produzione

Contiene:

- dati read-only della produzione selezionata
- bucket applicativo
- stato produzione computato
- eventuale evidenza del flag `forza_completata`

Nel primo slice la colonna destra e solo informativa.

## Data Semantics

### Read-only

Nel primo slice UI tutti i dati della surface `produzioni` sono esposti come read-only.

Questo include:

- dati provenienti dai mirror Easy tramite il `core`
- `bucket`
- `stato_produzione`
- `forza_completata`

### Configurable

Fuori scope nel primo slice UI:

- modifica del flag `forza_completata`
- configurazioni operative di produzione

## Selection Flow

- nessuna produzione selezionata -> colonna 2 in stato vuoto guidato
- produzione selezionata -> popolamento colonna 2
- cambio selezione -> refresh coerente del pannello di dettaglio

## UX Notes

- la surface `produzioni` nasce come vista consultiva
- il `bucket` deve risultare chiaramente distinguibile: `active` vs `historical`
- lo `stato_produzione` deve risultare chiaramente distinguibile: `attiva` vs `completata`
- la UI non deve ricostruire il calcolo dello stato; deve consumare il dato gia esposto dal `core`

## Notes

- Questa spec descrive il primo caso `produzioni` come variante a `2 colonne`.
- Eventuali filtri per `bucket`, `stato` o override manuale potranno essere introdotti in task successivi.

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`
