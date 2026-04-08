# DL-ARCH-V2-016 - Inventory / giacenza articoli come computed fact canonico

## Status
Approved

## Date
2026-04-08

## Context

La V2 ha introdotto:

- mirror sync read-only come base tecnica delle integrazioni Easy
- computed fact nel `core` quando il dato non esiste come campo canonico in sorgente
- separazione esplicita tra `sync`, `core` e `app`

Nel caso del magazzino, Easy non espone direttamente una giacenza canonica per articolo.
Espone invece movimenti di magazzino con quantita caricate e scaricate.

Per la V2 serve introdurre una prima entita canonica e riusabile di inventario,
da usare come building block condiviso e non come logica locale di un singolo modulo.

Questa entita dovra poter essere consumata in futuro da:

- lancio produzione
- viste di fabbisogni scoperti
- viste di riordino/reintegro
- futura allocazione supply/demand
- future funzionalita logistiche e di magazzino

## Decision

La V2 introduce `inventory` / `inventory position` / `on hand stock`
come primo computed fact canonico di giacenza per articolo.

Il modello e:

- `sync` = mirror dei movimenti grezzi di magazzino
- `core` = aggregazione canonica dei movimenti in giacenza netta per articolo
- `app` = consumo della posizione di giacenza, non dei movimenti grezzi

## 1. Formula canonica

La formula canonica iniziale e:

`on_hand_qty = sum(load_qty) - sum(unload_qty)`

Nel lessico V2:

- `load_qty` = quantita caricate
- `unload_qty` = quantita scaricate

Regola:

> La giacenza e un computed fact, non un campo sorgente diretto di Easy.

## 2. Perimetro V1

La V1 della giacenza e definita come:

- stock netto fisico per articolo

Livello di aggregazione iniziale:

- per `article_code`

Esplicitamente fuori scope in V1:

- multi-magazzino
- locations
- lotti
- stock bloccato
- prenotazioni
- allocazioni cliente
- disponibilita prospettica
- ATP / available-to-promise

Terminologia da usare:

- `inventory`
- `inventory position`
- `on hand stock`

Terminologia da non usare ancora:

- `available stock`

## 3. Confine tra Sync e Core

### Sync

Il layer `sync` deve costruire un mirror dei movimenti di magazzino con campi il piu possibile vicini alla sorgente Easy.

Il layer `sync`:

- non calcola giacenza
- non aggrega per articolo
- non introduce disponibilita o semantiche operative

### Core

Il layer `core` costruisce una computed fact canonica, ad esempio:

- `inventory_positions`

Questa fact e il primo output riusabile per i moduli applicativi.

Regola:

> I moduli applicativi consumano la posizione inventariale canonica, non i movimenti grezzi.

## 4. Modello dati guida

### Sync side

Il mirror dei movimenti puo includere, in forma il piu possibile fedele alla sorgente:

- `movement_id`
- `article_code`
- `movement_date`
- `load_qty`
- `unload_qty`
- `movement_type` o `cause`
- riferimenti documento sorgente
- sync metadata

### Core side

La computed fact `inventory_positions` puo includere almeno:

- `article_code`
- `total_load_qty`
- `total_unload_qty`
- `on_hand_qty`
- `computed_at`
- `source_last_movement_date`

Campi debug utili ma opzionali:

- `movement_count`

## 5. Business Rules

### Rule 1

L'inventory e una computed fact, non un campo diretto di Easy.

### Rule 2

L'inventory V1 rappresenta solo stock netto fisico.

### Rule 3

L'inventory V1 non include:

- commitments
- allocazioni
- prenotazioni cliente
- stock bloccato
- supply di produzione
- disponibilita prospettica

### Rule 4

L'inventory deve restare riusabile e indipendente da logiche locali di `production launch`.

## 6. Sync strategy per movimenti

Per `MAG_REALE` la direzione iniziale prevista e:

- mirror `append-only`
- acquisizione incrementale dei nuovi movimenti
- rebuild completo accettabile e previsto a intervalli noti

Questo significa:

- il `sync` dei movimenti puo essere incrementale
- la computed fact `inventory_positions` deve restare rebuildabile in modo deterministico

Regola:

> L'incremental sync dei movimenti non sostituisce la possibilita di rebuild completo della giacenza.

## 7. Rebuild policy

Per V1 e accettabile:

- rebuild completo della giacenza partendo dai movimenti sincronizzati

Quando verra introdotto lo scheduler, la V2 potra prevedere:

- rebuild completo periodico a intervalli noti
- esempio iniziale: una volta al giorno in fascia controllata

Il rebuild periodico non autorizza scritture verso Easy.

## 8. Cross-source normalization

Per il dominio magazzino, il confronto tra movimenti e anagrafica articoli puo richiedere normalizzazione tecnica del codice articolo.

Regola iniziale:

- trim spazi
- rimozione spazi non significativi dove necessario
- conversione a maiuscolo

Il collegamento tecnico tra:

- `MAG_REALE.ART_COD`
- `ANAART.ART_COD`

deve avvenire su codice normalizzato.

Questa e una normalizzazione tecnica, non una correzione business della sorgente.

## Consequences

### Positive

- introduzione di una computed fact canonica e riusabile
- separazione chiara tra movimenti grezzi e posizione di inventario
- base corretta per futuri moduli di produzione e magazzino
- modello compatibile con sync incrementale e rebuild deterministico

### Negative / Trade-off

- necessita di mantenere due livelli distinti: movimenti e posizione aggregata
- costo di rebuild completo della giacenza da considerare nel runtime futuro
- disponibilita e allocazioni restano da costruire sopra la giacenza canonica

## Impatto sul progetto

Questo DL prepara:

- il sync dei movimenti `MAG_REALE`
- il primo `core inventory_positions`
- i futuri moduli che useranno la giacenza come input condiviso

Non autorizza ancora:

- disponibilita promettibile
- logiche di allocazione
- politiche di riordino
- semantiche multi-magazzino

## Notes

- Questo DL e strutturale e non locale a `produzione`.
- `inventory` / `giacenza` e un building block condiviso del `core`.
- La V1 privilegia correttezza semantica e riuso, non ottimizzazione prematura.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/EASY_MAG_REALE.md`
