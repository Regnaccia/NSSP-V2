# STOCK_POLICY_V1_REDUCED_SPEC

## 1. Contesto

La V2 dispone gia di:

- `Planning Candidates`
- `future_availability_qty`
- planning policy con:
  - default a livello famiglia
  - override a livello articolo
  - `planning_mode`

Il prossimo passo naturale e introdurre una prima logica di `scorta` senza aprire ancora
`Production Proposals`.

La stock policy V1 deve:

- restare coerente con il planning attuale
- evitare hardcode di logiche
- evitare doppio conteggio tra shortage cliente e reintegro scorta

## 2. Obiettivo della V1

Introdurre una prima stock policy minimale che permetta di:

- calcolare una `scorta target`
- calcolare una soglia di trigger
- usare questi valori solo per gli articoli in `planning_mode = by_article`
- estendere in futuro `Planning Candidates` con un driver stock-driven

## 3. Scope V1

### La V1 FA

- introduce configurazioni stock di default a livello famiglia
- introduce override stock a livello articolo
- introduce una metrica di `capacity` solo a livello articolo
- introduce un algoritmo sostituibile per stimare la base mensile di scorta
- calcola:
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`

### La V1 NON FA ancora

- non introduce stagionalita
- non introduce family default per la `capacity`
- non introduce algoritmi multipli selezionabili in UI
- non introduce consumo stock-driven nel ramo `by_customer_order_line`
- non introduce ancora `Production Proposals`

## 4. Perimetro logico

La stock policy V1 vale solo per:

- `planning_mode = by_article`

Non vale per:

- `planning_mode = by_customer_order_line`

Conseguenza:

- non serve un flag separato `has_stock_policy`
- il prerequisito naturale della stock policy e stare nel ramo `by_article`

## 5. Configurazione V1

### Default famiglia

Campi proposti:

- `stock_months`
- `stock_trigger_months`

Questi valori hanno senso solo se il `planning_mode` effettivo dell'articolo e:

- `by_article`

### Override articolo

Campi proposti:

- `override_stock_months`
- `override_stock_trigger_months`
- `capacity_override_qty`

### Valori effettivi

Il Core `articoli` dovra in futuro poter esporre:

- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`

Regole:

- `effective_stock_months`:
  - override articolo se presente
  - altrimenti default famiglia
- `effective_stock_trigger_months`:
  - override articolo se presente
  - altrimenti default famiglia
- `capacity_effective_qty`:
  - `capacity_override_qty` se presente
  - altrimenti `capacity_calculated_qty`

Nota:

- la `capacity` e proprieta dell'articolo, non della famiglia
- quindi non esiste un `family capacity default`

## 6. Metrica base mensile

La stock policy V1 introduce una stima di:

- `monthly_stock_base_qty`

Definizione:

- quantita mensile minima di riferimento usata per derivare target e trigger

Origine:

- calcolata a partire dai movimenti storici Easy rilevanti

Vincolo architetturale:

- l'algoritmo di calcolo deve essere sostituibile
- non va hardcoded direttamente nei moduli operativi

Forma concettuale:

- `estimate_monthly_stock_base(context) -> qty`

L'algoritmo specifico V1 verra fissato nei task attuativi.

## 7. Capacity

La V1 introduce:

- `capacity_calculated_qty`
- `capacity_override_qty`
- `capacity_effective_qty`

Regola:

- `capacity_effective_qty = capacity_override_qty` se presente
- altrimenti `capacity_effective_qty = capacity_calculated_qty`

Scopo:

- compensare dati Easy mancanti o non affidabili
- mantenere separato il valore calcolato da quello operativo effettivo

## 8. Formule V1

### Target stock

- `target_stock_qty = min(capacity_effective_qty, effective_stock_months * monthly_stock_base_qty)`

### Trigger stock

- `trigger_stock_qty = effective_stock_trigger_months * monthly_stock_base_qty`

### Quantita operativa da confrontare

La stock policy V1 non introduce un nuovo nome.

Usa direttamente:

- `future_availability_qty`

gia esistente in `Planning Candidates by_article`.

### Regola di trigger

Scatta un fabbisogno stock-driven se:

- `future_availability_qty < trigger_stock_qty`

## 9. Caso limite da evitare

Caso:

- giacenza = `100`
- impegno cliente = `150`
- produzione in corso = `0`
- `future_availability_qty = -50`
- `target_stock_qty = 500`

Errore da evitare:

- aprire due candidate distinti:
  - uno per shortage cliente
  - uno per scorta

La regola corretta V1 e:

- un solo candidate `by_article`
- con due componenti interne:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`

Formule:

- `customer_shortage_qty = max(-future_availability_qty, 0)`
- `stock_replenishment_qty = max(target_stock_qty - max(future_availability_qty, 0), 0)`
- `required_qty_total = customer_shortage_qty + stock_replenishment_qty`

Questa forma:

- evita doppio conteggio
- mantiene un solo candidate per articolo
- prepara bene l'eventuale passaggio futuro a `Production Proposals`

## 10. Output atteso V1

La V1 deve preparare un building block stock-driven riusabile, non ancora la UI finale.

Campi attesi nel futuro read model / computed fact:

- `article_code`
- `monthly_stock_base_qty`
- `capacity_calculated_qty`
- `capacity_effective_qty`
- `target_stock_qty`
- `trigger_stock_qty`
- `computed_at`
- `algorithm_key`

## 11. Principio architetturale

La logica di scorta segue la stessa regola generale gia adottata in V2:

- i fact restano stabili
- le logiche che li interpretano sono sostituibili

Quindi:

- il calcolo della base mensile
- il calcolo di target/trigger
- la decisione di fabbisogno stock-driven

devono restare implementati come funzioni o policy sostituibili, non come formule sparse.

## 12. Esclusioni esplicite

Fuori scope per questa V1:

- safety stock dinamica
- stagionalita
- previsioni avanzate
- modelli predittivi
- parametri per famiglia diversi dalla policy stock minima
- stock policy nel ramo `by_customer_order_line`

## 13. Sintesi finale

La stock policy V1 ridotta e:

- solo `by_article`
- senza `family capacity default`
- con:
  - `stock_months`
  - `stock_trigger_months`
  - `capacity_override_qty`
- basata su:
  - `monthly_stock_base_qty`
  - `future_availability_qty`
- con candidato unico per articolo e breakdown interno:
  - shortage cliente
  - replenishment scorta
