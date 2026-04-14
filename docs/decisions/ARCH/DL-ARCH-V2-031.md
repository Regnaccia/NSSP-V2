# DL-ARCH-V2-031 - Customer horizon, stock horizon e separazione UI dei driver planning

## Status

Accepted

## Date

2026-04-13

## Context

`Planning Candidates` oggi unifica gia nel ramo `by_article` due componenti:

- `customer_shortage_qty`
- `stock_replenishment_qty`

Questa unificazione e corretta a livello Core per evitare doppio conteggio e preparare bene i
futuri `Production Proposals`.

Restano pero due problemi distinti:

1. in UI i candidate customer-driven e stock-driven hanno semantiche operative diverse e devono
   essere leggibili separatamente
2. la componente stock-driven non deve reagire a impegni troppo lontani nel tempo
3. la componente customer-driven puo richiedere un primo filtro temporale semplice basato su
   `data_consegna`, senza ancora introdurre lead time o scheduling

## Decision

### 1. Il Core `Planning Candidates` resta unico

Non vengono introdotti due moduli o due projection distinte per:

- fabbisogno cliente
- scorta

Nel ramo `by_article` resta un solo candidate per articolo, con breakdown interno:

- `customer_shortage_qty`
- `stock_replenishment_qty`
- `required_qty_total`

### 2. La separazione tra fabbisogno e scorta avviene in UI

La vista `Planning Candidates` deve poter filtrare i candidate `by_article` almeno in tre modi:

- `Tutti`
- `Solo fabbisogno cliente`
- `Solo scorta`

Regole minime:

- `Solo fabbisogno cliente`:
  - `primary_driver = customer`
- `Solo scorta`:
  - `primary_driver = stock`

Questo e un filtro di presentazione, non una biforcazione del Core.

### 2.1 I casi misti hanno precedenza `customer`

Nel ramo `by_article` un candidate puo avere entrambe le componenti attive:

- `customer_shortage_qty > 0`
- `stock_replenishment_qty > 0`

In questo caso:

- il candidate resta unico
- la UI deve mostrare entrambe le componenti
- la classificazione primaria della riga deve essere:
  - `customer`

Regola:

1. se `customer_shortage_qty > 0`
   - `primary_driver = customer`
2. altrimenti, se `stock_replenishment_qty > 0`
   - `primary_driver = stock`

Conseguenza:

- un candidate misto compare nella scheda `customer`
- non compare anche nella scheda `stock`

### 2.2 `required_qty_minimum` segue il driver primario

Nel ramo `by_article`, `required_qty_minimum` deve restare coerente con il driver primario della
riga.

Regola:

- se `primary_driver = customer`
  - `required_qty_minimum = customer_shortage_qty`
- se `primary_driver = stock`
  - `required_qty_minimum = stock_replenishment_qty`

Quindi, nel caso `stock-only`, il fabbisogno minimo non resta vuoto e coincide con la scopertura
minima di scorta rispetto a `target_stock_qty`.

### 2.3 La data richiesta in UI segue il driver cliente reale

La tabella `Planning Candidates` puo esporre una colonna data per aumentare la leggibilita, ma la
semantica non e identica nei due rami.

Regola:

- `by_customer_order_line`
  - mostra la `requested_delivery_date` della riga ordine
- `by_article`
  - mostra la `earliest_customer_delivery_date`
  - il campo e valorizzato solo se il candidate ha una componente customer
  - nei casi `stock-only` il campo resta `null`

Conseguenza:

- la UI non deve inventare una data per candidate puramente stock-driven
- la futura semantica `earliest_uncovered_due_date` resta un'evoluzione successiva, fuori scope V1

### 2.4 La descrizione per-riga deriva dal Core ordini, non da concatenazioni UI

Nel ramo `by_customer_order_line` il mirror e il Core ordini gia distinguono:

- segmento principale della riga
- righe descrittive di continuazione aggregate

Decisione:

- il Core `Planning Candidates` deve esporre un campo esplicito:
  - `full_order_line_description`
- questo campo deriva da:
  - `article_description_segment`
  - `description_lines`

Conseguenza:

- la UI planning non deve ricostruire la descrizione completa lato frontend
- la descrizione primaria del candidate per-riga usa `full_order_line_description`

### 2.5 La destinazione richiesta segue la richiesta cliente quando esiste

La vista planning puo esporre anche la destinazione della richiesta, ma solo con semantica
esplicita e spiegabile.

Decisione:

- `by_customer_order_line`
  - la destinazione deriva dalla riga ordine cliente
  - il testo mostrato usa:
    - `nickname_destinazione`, se presente
    - altrimenti la label di default della destinazione
- `by_article`
  - la destinazione puo essere esposta solo se associabile in modo non ambiguo alla richiesta
    cliente che guida la data mostrata
  - se il mapping non e univoco:
    - `requested_destination_display = "Multiple"`
  - nei casi `stock-only`:
    - `requested_destination_display = null`

### 2.6 La leggibilita UI usa badge, non semantiche duplicate

Per migliorare la leggibilita del modulo planning:

- `famiglia_label` puo essere resa come badge con palette centralizzata
- `primary_driver` e i motivi attivi possono essere resi come badge sintetici
- i casi misti mostrano sia `Cliente` sia `Scorta`, ma restano una sola riga e una sola
  appartenenza primaria

Questo e un refinement di presentazione, non una modifica del modello canonico del candidate.

### 2.7 I warning articolo possono essere consumati nella vista planning

Poiche il planning `by_article` puo evidenziare fabbisogni stock-driven, la vista planning puo
mostrare anche gli warning attivi collegati all'articolo.

Regola:

- `Planning Candidates` non genera warning propri
- consuma warning canonici del modulo `Warnings`
- la visibilita dei warning in planning resta governata da:
  - `visible_to_areas`
  - area corrente dell'utente

Primo warning di riferimento:

- `INVALID_STOCK_CAPACITY`

### 2.8 Il quick edit planning riusa il dominio `articoli`

La vista planning puo offrire una quick action di configurazione articolo per ridurre il tempo di
correzione degli errori configurativi.

Regola:

- la quick action apre un modal o entry point rapido
- il modal riusa i contract e la semantica della surface `articoli`
- non viene introdotto un secondo dominio di configurazione planning-specifico

Perimetro minimo della quick action:

- famiglia articolo
- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`
- `capacity_override_qty`

### 3. Il customer-driven introduce un primo `customer horizon`

La componente customer-driven puo essere valutata anche rispetto a un primo orizzonte temporale
operativo semplice.

Configurazione iniziale:

- `customer_horizon_days`

Semantica V1:

- basata solo su `data_consegna`
- senza lead time, tempi ciclo o capacità

Il Core non deve eliminare i candidate fuori orizzonte.

Deve invece esporre un flag minimo:

- `is_within_customer_horizon`

Regola concettuale:

```text
is_within_customer_horizon = delivery_date <= today + customer_horizon_days
```

La UI puo usare questo flag per offrire un filtro:

- `solo entro customer horizon`

### 4. La componente stock-driven introduce un `stock horizon`

La componente stock-driven non deve reagire a domanda cliente troppo lontana.

In V1 il `look-ahead` stock sugli impegni viene limitato a:

- `effective_stock_months`

Forma concettuale:

- `stock_lookahead_months = effective_stock_months`
- `capped_commitments_qty`:
  - impegni cliente con `data_consegna` entro `today + stock_lookahead_months`

La disponibilita usata per la sola componente scorta diventa:

```text
stock_horizon_availability_qty =
  inventory_qty
  - customer_set_aside_qty
  - capped_commitments_qty
  + incoming_supply_qty
```

La componente customer-driven continua invece a usare la logica customer standard del modulo.

### 5. Regola di calcolo aggiornata della componente stock

La formula della componente stock-driven diventa:

```text
stock_replenishment_qty =
  max(target_stock_qty - max(stock_horizon_availability_qty, 0), 0)
```

La formula customer-driven resta:

```text
customer_shortage_qty = max(-future_availability_qty, 0)
```

## Consequences

### Positive

- si evita che la scorta reagisca a ordini troppo lontani
- si mantiene un Core unico e coerente
- la UI puo separare bene i due driver senza duplicare la projection
- si apre un primo concetto di orizzonte customer senza introdurre scheduling prematuro

### Tradeoffs

- il ramo `by_article` espone piu campi e semantiche
- si introducono due horizon distinti:
  - `customer horizon`
  - `stock horizon`
- la logica customer a lungo termine resta ancora semplice e basata solo su `data_consegna`

## Out of Scope

- lead time produttivi
- tempi ciclo
- capacità macchina
- schedulazione
- ETA avanzata delle produzioni
- ranking/prioritizzazione

## References

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
