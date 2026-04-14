# BUG: `core_articolo_config` puo creare record orfani per articoli inesistenti

**Data rilevazione**: 2026-04-13
**Rilevato da**: review tecnica progetto V2
**Severity**: Alta - puo persistere configurazione interna incoerente e restituire `404` dopo `commit`

---

## Sintomo

Alcuni endpoint `PATCH` della surface `produzione` accettano un `codice_articolo`
che non esiste nel mirror `sync_articoli`, ma scrivono comunque su
`core_articolo_config`.

Effetti osservabili:

- `PATCH /api/produzione/articoli/{codice}/famiglia` puo restituire `204 No Content`
  anche se l'articolo non esiste
- gli altri `PATCH` di override possono fare `commit` e poi rispondere `404`
- il database puo accumulare record interni non collegati ad alcun articolo reale

## Evidenza nel codice

Gli endpoint applicativi fanno `commit` prima di verificare in modo coerente
l'esistenza dell'articolo:

- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:344)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:380)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:413)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:444)

Le funzioni Core creano `CoreArticoloConfig` se assente senza verificare che
`codice_articolo` esista in `sync_articoli`:

- [queries.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py:482)
- [queries.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py:526)
- [queries.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py:560)
- [queries.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py:589)

Il modello esplicita inoltre che `core_articolo_config` non ha una FK hard verso
`sync_articoli`:

- [models.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/models.py:64)

## Causa radice

Il layer Core tratta `core_articolo_config` come storage interno indipendente dal
mirror `sync_articoli`.

Questa scelta e legittima come boundary architetturale, ma nel codice attuale manca
un'invariante applicativa equivalente:

- nessun controllo esplicito di esistenza articolo prima della scrittura
- nessun vincolo DB che blocchi codici inesistenti
- ordine sbagliato nel router: `commit` prima della verifica finale del dettaglio

Il risultato e che una typo o una chiamata API manuale puo inserire configurazione
interna per un articolo che il sistema non conosce.

## Impatto

- stato interno incoerente tra `sync_articoli` e `core_articolo_config`
- `404` restituita dopo una mutazione gia persa nel database
- rischio di debugging difficile su override "fantasma"
- rischio di propagare assunzioni sbagliate in report, cleanup futuri o query Core

## Ambito affetto

Endpoint affetti:

- `PATCH /api/produzione/articoli/{codice}/famiglia`
- `PATCH /api/produzione/articoli/{codice}/policy-override`
- `PATCH /api/produzione/articoli/{codice}/stock-policy-override`
- `PATCH /api/produzione/articoli/{codice}/gestione-scorte-override`

## Direzione di risoluzione

Fix applicativo minimo:

1. verificare l'esistenza dell'articolo in `sync_articoli` prima di ogni write
2. fallire con `404` prima di fare `commit`
3. aggiungere test HTTP e/o Core che coprano il caso "codice inesistente"

Fix strutturale possibile:

- introdurre una guard condivisa `assert_articolo_exists(...)`
- valutare se mantenere davvero l'assenza di FK hard oppure introdurre almeno
  una validazione coerente lato Core

## Note

Questo problema e distinto dai codici orfani nei moduli read-only tipo `criticita`:
qui il problema non e il join di lettura, ma la possibilita di creare nuovo stato
interno su un codice articolo inesistente.
