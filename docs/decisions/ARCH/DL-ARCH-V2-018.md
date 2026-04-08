# DL-ARCH-V2-018 - Ordine come entita canonica cross-modulo

## Status
Approved

## Date
2026-04-08

## Context

Con `DL-ARCH-V2-017` la V2 ha introdotto `impegno` come computed fact canonico del Core.

Una delle prime provenienze previste per `commitments` e:

- `customer_order`

Questo rende necessario esplicitare un nuovo building block di dominio:

- `ordine`

`Ordine` non deve nascere come concetto locale del solo modulo `produzione`.
E una entita operativa trasversale che potra essere consumata da piu aree, ad esempio:

- produzione
- commerciale
- logistica
- disponibilita futura

Se `ordine` resta implicito nella sola logica di `impegno`, il progetto rischia di:

- duplicare letture e regole in moduli diversi
- legare gli ordini a un singolo reparto
- perdere un riferimento canonico per righe ordine, stato apertura e riferimenti cliente/articolo

## Decision

La V2 introduce `ordine` come entita canonica del `core`, distinta da:

- `commitments`
- `inventory`
- logiche specifiche di singoli moduli

Il modello prevede:

- mirror sync read-only delle sorgenti Easy relative agli ordini
- Core `ordini` come rappresentazione canonica riusabile
- computed fact `commitments` cliente costruita sopra le righe ordine aperte, non direttamente sul mirror sync

## 1. Definizione

Nel lessico V2:

- `ordine`
- `riga_ordine`
- `customer_order`
- `customer_order_line`

`Ordine` e una entita operativa che rappresenta una domanda cliente tracciabile.

La granularita minima utile per il Core e la `riga_ordine`, perche:

- gli impegni cliente nascono tipicamente a livello riga
- articolo, quantita e stato apertura vivono a quel livello

Regola:

> La riga ordine e il building block operativo minimo; l'ordine aggrega e contestualizza.

## 2. Separazione dei layer

### Sync

Il layer `sync` deve:

- costruire mirror tecnici read-only delle tabelle Easy sorgente
- mantenere i dati il piu vicini possibile alla sorgente
- non calcolare ancora `commitments`

### Core

Il layer `core` deve:

- esporre `ordini` e `righe_ordine` come entita canoniche riusabili
- applicare eventuali normalizzazioni o join necessarie tra header e righe
- fornire la base per costruire `commitments` cliente

### App

I moduli applicativi devono consumare:

- `ordini` / `righe_ordine` canonici
- oppure `commitments`

e non i mirror sync grezzi.

Regola:

> I moduli non ricostruiscono gli ordini leggendo direttamente le tabelle Easy mirrorate.

## 3. Neutralita cross-modulo

`Ordine` e una entita multi reparto.

Non deve essere modellato:

- come sottoinsieme di `produzione`
- come dettaglio secondario della sola `logistica`
- come scorciatoia per calcolare soltanto `impegni`

Deve restare riusabile da piu stream futuri, ad esempio:

- stato ordini cliente
- impegni cliente
- disponibilita
- pianificazione
- avanzamenti operativi collegati

## 4. Relazione con commitments

Gli impegni cliente non nascono direttamente dalla sorgente Easy grezza.

La sequenza corretta e:

1. mirror sync ordini
2. Core `ordini` / `righe_ordine`
3. computed fact `commitments` da righe ordine aperte

Regola:

> `customer_order` e una sorgente canonica per `commitments`, non un sostituto della fact `commitments`.

## 5. Livello minimo V1

Per la V1 del dominio `ordini` il perimetro minimo e:

- cliente
- riga ordine
- articolo
- quantita
- riferimenti ordine
- stato di apertura utile al calcolo impegni

Nel primo slice non e necessario introdurre subito:

- workflow commerciale avanzato
- gestione prezzi
- gestione consegne multi-step
- allocazioni
- disponibilita promessa

## 6. Entita canoniche previste

Il Core potra esporre almeno:

- `customer_orders`
- `customer_order_lines`

o nomi equivalenti, purche sia chiara la distinzione tra:

- testata ordine
- riga ordine

Campi canonici attesi in V1:

- `order_reference`
- `line_reference`
- `customer_code`
- `article_code`
- `ordered_qty`
- `open_qty` o dato equivalente utile
- `order_status` o stato minimo di apertura
- `document_date` o riferimento temporale disponibile

La scelta esatta dei campi verra fissata nel mapping Easy e nei task attuativi.

## 7. Riuso futuro

Questa entita e introdotta per accelerare i futuri stream:

- commitments cliente
- disponibilita
- viste ordine cross-funzione
- integrazioni logistica/commerciale

L'obiettivo e evitare un modello dove ogni modulo reinterpreta gli ordini in modo autonomo.

## Consequences

### Positive

- ordini trattati come building block canonico e non come dettaglio locale
- base pulita per `commitments` cliente
- miglior riuso cross-modulo
- minore duplicazione di logica tra produzione, logistica e disponibilita

### Negative / Trade-off

- richiede un nuovo stream `sync + core` dedicato
- rimanda di poco il calcolo degli impegni cliente, per farlo nascere su una base piu pulita
- obbliga a chiarire bene la sorgente Easy e il livello header/riga

## Impatto sul progetto

Questo DL prepara:

- mapping Easy della sorgente ordini cliente
- futuri task di mirror sync ordini
- futuri task Core `ordini`
- futuri task `commitments` cliente

Non introduce ancora:

- task attuativi
- disponibilita
- allocazioni
- UI ordini

## Notes

- `Ordine` nasce come entita canonica cross-modulo.
- Il primo obiettivo non e la UI ordine, ma una base Core riusabile per stream futuri.
- La granularita riga ordine e centrale per i futuri `commitments` cliente.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
