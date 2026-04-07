# DL-ARCH-V2-012 - Destinazione principale derivata dal cliente

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

Nel modello Easy attuale:

- `ANACLI` rappresenta l'anagrafica cliente
- `POT_DESTDIV` rappresenta eventuali destinazioni aggiuntive del cliente

Operativamente, il cliente stesso continua pero a fungere da destinazione principale implicita.

Questo significa che, anche in assenza di righe in `POT_DESTDIV`, un cliente ha comunque un punto operativo valido corrispondente ai propri dati anagrafici.

Se questa regola non viene esplicitata nel Core, il rischio e:

- trattare come "senza destinazioni" clienti che in realta hanno una destinazione principale
- costringere la UI a dedurre logiche di dominio a partire da `sync_clienti`
- rendere incompleto l'elenco operativo delle destinazioni

Questo DL nasce come raffinamento del primo slice Core definito in `DL-ARCH-V2-010`, che aveva introdotto il modello `clienti + destinazioni` senza rendere ancora esplicita la principale derivata dal cliente.

## Decision

La V2 tratta il record cliente in `ANACLI` come una destinazione principale esplicita nel layer Core.

Regola:

- ogni cliente genera sempre una destinazione principale derivata dai dati cliente
- le righe di `POT_DESTDIV` restano destinazioni aggiuntive esplicite
- la surface e i read model Core devono lavorare su un elenco destinazioni unificato

Il layer `sync` non viene modificato:

- `sync_clienti` continua a riflettere `ANACLI`
- `sync_destinazioni` continua a riflettere `POT_DESTDIV`

La promozione della destinazione principale avviene nel Core.

## 1. Destinazione principale sempre presente

Per ogni cliente esiste una destinazione principale derivata dai campi anagrafici del cliente.

Questa destinazione:

- e implicita nella sorgente Easy
- diventa esplicita nel modello Core
- deve comparire nell'elenco destinazioni del cliente

Conseguenza:

- un cliente non e mai privo di destinazioni operative nel primo slice, anche se non ha righe in `POT_DESTDIV`

## 2. Distinzione tra principale e aggiuntive

Nel Core esistono due tipi logici di destinazione:

- destinazione principale derivata dal cliente
- destinazioni aggiuntive derivate da `sync_destinazioni`

Regola:

- la distinzione deve essere esplicita nel read model
- la UI non deve dedurre da sola quale destinazione sia principale

## 3. Origine dei dati della principale

La destinazione principale deriva dai dati di `sync_clienti`.

Campi minimi derivabili nel primo slice:

- `codice_cli`
- `ragione_sociale`
- `indirizzo`
- `nazione_codice`
- `provincia`
- `telefono_1`

Solo i campi realmente presenti in `sync_clienti` possono essere usati.

Il Core non deve inventare campi assenti.

## 4. Identita Core della destinazione principale

La destinazione principale deve avere una identita Core stabile e distinta dalle destinazioni aggiuntive.

Regola:

- non usa `PDES_COD`, perche non proviene da `POT_DESTDIV`
- deve essere derivata deterministicamente dal cliente

Il formato tecnico esatto puo essere deciso nel task implementativo, ma deve garantire:

- unicita per cliente
- stabilita nel tempo
- distinguibilita rispetto alle destinazioni aggiuntive

## 5. Elenco destinazioni unificato

Il read model Core delle destinazioni del cliente deve includere:

1. la destinazione principale
2. le eventuali destinazioni aggiuntive

Regole:

- la principale deve risultare sempre presente
- l'ordinamento consigliato mette la principale prima delle aggiuntive
- il read model deve esporre un flag o attributo equivalente che identifichi la principale

## 6. Configurazione interna della principale

La destinazione principale deve poter partecipare allo stesso modello configurativo minimo delle altre destinazioni.

In particolare:

- `nickname_destinazione` deve poter esistere anche per la principale

Regola:

- la configurazione interna della principale vive nel Core, non nel layer `sync`
- la principale non e un caso speciale escluso dal modello configurativo

## 7. Impatto sui read model del Core

Il Core slice `clienti + destinazioni` deve essere aggiornato in modo che:

- la lista destinazioni per cliente includa sempre la principale
- il dettaglio destinazione supporti sia principale sia aggiuntive
- la UI possa mostrare chiaramente la principale come voce reale dell'elenco

Il read model deve rendere espliciti almeno:

- identificativo destinazione
- appartenenza al cliente
- `is_primary` o equivalente
- dati read-only derivati da Easy
- eventuale `nickname_destinazione`

## 8. Confine con il layer sync

Questa regola NON modifica i target sync.

Regole:

- `sync_clienti` non diventa un elenco destinazioni
- `sync_destinazioni` non deve contenere la principale artificiale
- la composizione principale + aggiuntive e responsabilita del Core

## 9. Confine con la UI

La UI clienti/destinazioni deve consumare l'elenco unificato prodotto dal Core.

La UI non deve:

- dedurre la destinazione principale dai dati cliente
- fondere direttamente `sync_clienti` e `sync_destinazioni`
- decidere da sola l'ordinamento semantico delle destinazioni

Regola:

- backend/Core produce il modello operativo
- frontend lo presenta

## Esclusioni

Questo DL NON definisce:

- formato tecnico definitivo dell'identificatore della principale
- stile visivo della principale nella UI
- configurazioni logistiche oltre `nickname_destinazione`
- eventuali policy future di merge o deduplicazione tra principale e aggiuntive

## Consequences

### Positive

- il modello operativo riflette meglio la logica reale di Easy
- i clienti risultano sempre navigabili anche senza destinazioni aggiuntive
- la UI riceve un elenco coerente e completo
- la configurazione Core resta uniforme tra principale e aggiuntive

### Negative / Trade-off

- introduce una destinazione non presente come record esplicito in `POT_DESTDIV`
- richiede una identita Core dedicata per la principale
- aumenta leggermente la complessita del read model

## Impatto sul progetto

Questo DL aggiorna il perimetro del primo slice Core clienti/destinazioni.

Deve guidare:

- l'implementazione di `TASK-V2-012`
- l'allineamento di `DL-ARCH-V2-010`
- la futura UI clienti/destinazioni

## Notes

- La principale e una promozione Core di un concetto gia presente operativamente in Easy.
- Le destinazioni aggiuntive restano integralmente governate da `POT_DESTDIV`.
- Il layer `sync` non va alterato per accomodare questa regola.
- Questo DL non sostituisce `DL-ARCH-V2-010`: ne raffina il perimetro sul tema delle destinazioni operative del cliente.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
