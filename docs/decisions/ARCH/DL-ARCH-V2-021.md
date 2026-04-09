# DL-ARCH-V2-021 - Availability come computed fact canonico derivato

## Status
Approved

## Date
2026-04-09

## Context

La V2 ha gia introdotto tre fact canonici distinti:

- `inventory`
- `commitments`
- `customer_set_aside`

Con `DL-ARCH-V2-016`, `DL-ARCH-V2-017` e `DL-ARCH-V2-019` il modello ha ormai separato in modo esplicito:

- stock fisico netto
- domanda operativa ancora aperta
- quota gia fisicamente appartata per cliente

Manca ora il derivato applicativo che esprima la quota effettivamente libera dopo questi assorbimenti.

Questo concetto non puo essere modellato correttamente come:

- `availability = inventory - commitments`

perche ignorerebbe la quota `customer_set_aside`, che resta fisicamente in stock ma non e piu libera.

## Decision

La V2 introduce `availability` come computed fact canonico del `core`, derivato dai tre fact gia esistenti:

- `inventory`
- `customer_set_aside`
- `commitments`

Nel perimetro V1, la formula canonica e:

- `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`

## 1. Definizione

`Availability` rappresenta la quota di articolo:

- fisicamente presente
- non gia appartata per cliente
- non gia assorbita da domanda operativa aperta

Regola:

> `Availability` e un fact canonico del `core`, non un campo raw Easy e non una deduzione locale di modulo.

## 2. Relazione con i fact precedenti

La V2 mantiene distinti:

- `inventory`
  - stock fisico netto
- `customer_set_aside`
  - quota fisicamente non libera per cliente
- `commitments`
  - domanda ancora da coprire operativamente
- `availability`
  - quota finale libera dopo le due riduzioni

Regola:

> `Availability` dipende dai tre fact precedenti, ma non li sostituisce e non li comprime.

## 3. Formula V1

Nel perimetro V1:

- `free_stock_qty = inventory_qty - customer_set_aside_qty`
- `availability_qty = free_stock_qty - committed_qty`

Equivalentemente:

- `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`

La V2 non materializza `free_stock` come fact canonico separato.
Resta un passaggio logico interno al calcolo di `availability`.

## 4. Aggregazione minima

La granularita canonica minima di `availability` e:

- per `article_code`

Nel V1 non vengono introdotti ancora:

- multi-magazzino
- lotti
- ubicazioni
- disponibilita per cliente
- disponibilita per data

## 5. Modello canonico minimo

Il fact canonico puo includere almeno:

- `article_code`
- `inventory_qty`
- `customer_set_aside_qty`
- `committed_qty`
- `availability_qty`
- `computed_at`

Campi opzionali utili:

- `inventory_computed_at`
- `set_aside_computed_at`
- `commitments_computed_at`
- `movement_count`
- `commitment_count`

## 6. Regole quantitative V1

Nel V1:

- i fact mancanti per uno specifico articolo valgono `0` nel calcolo
- il calcolo deve essere deterministico a parita di input
- la quantita puo risultare negativa

La V2 non applica ancora clamp automatici a zero.

Regola:

> una `availability` negativa e un'informazione utile, non un errore da nascondere.

## 7. Separazione da ATP e allocazioni

`Availability` V1 non equivale ancora a:

- ATP
- disponibilita promessa al cliente
- allocazione per priorita
- disponibilita datata

Non vengono introdotti ancora:

- criteri di priorita
- compensazioni avanzate
- simulazioni temporali

Regola:

> `Availability` V1 e una fotografia quantitativa corrente, non un motore di promessa o pianificazione.

## 8. Sorgenti corrette

`Availability` deve essere calcolata solo a partire dai fact canonici del `core`:

- `inventory_positions`
- `customer_set_aside`
- `commitments`

Non e ammesso costruirla:

- dai mirror sync grezzi
- da query UI ad hoc
- da formule duplicate nei moduli applicativi

## Consequences

### Positive

- chiude il primo triangolo canonico `inventory / set_aside / commitments`
- evita formule incoerenti replicate nei moduli
- prepara verifiche visive immediate nella surface `articoli`
- rende possibile una futura evoluzione verso ATP e stock policy

### Negative / Trade-off

- introduce un ulteriore fact derivato da mantenere
- aumenta la catena di refresh sequenziale delle surface che lo consumano
- richiede attenzione alla freshness dei tre fact sorgente

## Impatto sul progetto

Questo DL prepara:

- un task Core per `availability`
- una futura esposizione read-only nel dettaglio `articoli`
- un futuro refresh sequenziale esteso che ricalcoli anche `availability`

Non introduce ancora:

- UI dedicata magazzino/disponibilita
- ATP
- suggerimenti o alert automatici

## Notes

- `Availability` nasce dopo `customer_set_aside`, non al suo posto.
- `Free stock` resta un passaggio logico utile, ma non un fact canonico separato nel V1.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-020.md`
