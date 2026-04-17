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
- introduce una strategy selezionabile per stimare la base mensile di scorta
- introduce parametri configurabili per le logiche stock, senza hardcode nel codice
- calcola:
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`

### La V1 NON FA ancora

- non introduce stagionalita
- non introduce family default per la `capacity`
- non introduce selezione libera degli algoritmi dalla UI operativa
- non introduce consumo stock-driven nel ramo `by_customer_order_line`
- non introduce ancora `Production Proposals`

## 4. Perimetro logico

La stock policy V1 vale solo per:

- `planning_mode = by_article`
- `effective_gestione_scorte_attiva = true`

Non vale per:

- `planning_mode = by_customer_order_line`
- articoli `by_article` con gestione scorte disattivata

Conseguenza:

- non serve un flag separato `has_stock_policy`
- serve invece un flag operativo esplicito:
  - `gestione_scorte_attiva`

## 5. Configurazione V1

### Default famiglia

Campi proposti:

- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`

Questi valori hanno senso solo se il `planning_mode` effettivo dell'articolo e:

- `by_article`

### Override articolo

Campi proposti:

- `override_gestione_scorte_attiva`
- `override_stock_months`
- `override_stock_trigger_months`
- `capacity_override_qty`

### Valori effettivi

Il Core `articoli` dovra in futuro poter esporre:

- `effective_gestione_scorte_attiva`
- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`

Regole:

- `effective_gestione_scorte_attiva`:
  - override articolo se presente
  - altrimenti default famiglia
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
- il `planning_mode = by_article` resta prerequisito necessario ma non sufficiente:
  - la stock policy si applica solo con `effective_gestione_scorte_attiva = true`

## 6. Metrica base mensile

La stock policy V1 introduce una stima di:

- `monthly_stock_base_qty`

Definizione:

- quantita mensile minima di riferimento usata per derivare target e trigger

Origine:

- calcolata a partire dai movimenti storici gia sincronizzati nei mirror V2
- in V1 la sorgente operativa e:
  - `sync_mag_reale`
- non si leggono dati direttamente da Easy dentro questa logica

Vincolo architetturale:

- la logica deve essere selezionabile per `strategy_key`
- la selezione deve avvenire da configurazione interna V2, non da hardcode
- i parametri numerici della logica devono essere configurabili
- la strategy deve essere risolta contro un registry chiuso nel codice

Forma concettuale:

- `estimate_monthly_stock_base(strategy_key, params, context) -> qty`

Strategia iniziale prevista:

- `monthly_stock_base_from_sales_v1`

### Profilo algoritmico concordato per `monthly_stock_base_from_sales_v1`

La prima strategy V1 deve essere descritta in modo preciso cosi:

- perimetro articoli:
  - solo articoli con `planning_mode = by_article`
- sorgente dati:
  - mirror interno `sync_mag_reale`
- driver movimenti:
  - in V1 contano tutte le righe con `quantita_scaricata > 0`
  - non si applica ancora un filtro esplicito su `causale_movimento_codice`
- quantita usata:
  - quantita scaricata / consumo rilevante per articolo
- granularita:
  - consumo mensile per articolo
- finestre temporali iniziali:
  - `12 mesi`
  - `6 mesi`
  - `3 mesi`
- per ogni finestra:
  - si raccolgono i movimenti nel perimetro temporale
  - si applica filtro outlier con soglia configurabile
  - si aggregano i consumi per mese
  - si calcola il percentile configurato sui consumi mensili
- risultato finale:
  - media dei risultati ottenuti sulle finestre attive

### Parametri configurabili della strategy

I parametri numerici non devono essere hardcoded e devono vivere nella configurazione
interna delle logiche stock.

Parametri previsti per V1:

- `min_movements`
- `zscore_threshold`
- `percentile`
- `windows_months`
- `rounding_scale`
- `min_nonzero_months`

### Fallback e comportamento atteso

- se lo storico e insufficiente rispetto ai parametri minimi configurati:
  - `monthly_stock_base_qty = None` in V1
- se non esistono movimenti rilevanti nel periodo:
  - `monthly_stock_base_qty = None`
- `None` significa:
  - base mensile incalcolabile per dati insufficienti
- `0` significa:
  - consumo reale zero, se la strategia produce esplicitamente quel risultato
- il rounding finale e parametrico
- la strategy deve restare sostituibile, ma il profilo sopra e il riferimento V1 concordato

### Strategy aggiuntive introdotte dopo l'analisi dei dati reali

Dopo l'analisi dei dati reali (`2026-04-17`) sono state aggiunte due strategy ulteriori al registry.
Le strategy coesistono nel codice; una sola e attiva alla volta tramite `monthly_base_strategy_key`.

---

#### `monthly_stock_base_weighted_v2`

Identica a `v1` nella struttura (multi-finestra, z-score, percentile), ma sostituisce la media
semplice delle stime per finestra con una **media pesata**.

Motivazione:

- in `v1` la finestra 12m e la finestra 3m pesano uguale
- per articoli con trend in corso (crescita o calo) la media semplice diluisce il segnale recente
- pesi crescenti verso le finestre piu recenti seguono meglio il mercato

Parametri aggiuntivi rispetto a `v1`:

| Parametro | Default | Significato |
|-----------|---------|-------------|
| `window_weights` | `[1, 2, 3]` | Peso per ogni finestra (allineato a `windows_months`) |

Comportamento:

- result = `sum(stima_i * peso_i) / sum(pesi_validi)`
- finestre che non superano la validazione (`min_nonzero_months`) sono escluse sia dalla somma che dal denominatore
- tutti gli altri parametri (`percentile`, `zscore_threshold`, ecc.) identici a `v1`

---

#### `monthly_stock_base_segmented_v1`

Approccio radicalmente diverso da `v1`/`v2`: classifica ogni articolo per continuita della
domanda nel periodo di lookback e applica una **formula diversa per segmento**.

Motivazione:

- l'analisi dei dati reali ha mostrato che il 47.6% degli articoli nel perimetro e dormante
  (zero movimenti in 12 mesi), il 45% ha domanda intermittente (1-7 mesi su 12)
- per gli articoli intermittenti il zero-fill (riempire i mesi vuoti con 0 e calcolare il percentile)
  abbassa sistematicamente la stima: tratta l'assenza di vendite come "consumo zero" invece che come
  "questo articolo non e stato toccato questo mese"
- la domanda giusta per un articolo intermittente non e "quanto vendo per mese?" ma
  "quanto ho venduto in totale nel periodo, distribiuto sui mesi?"

Classificazione articoli (in base ai mesi con `quantita_scaricata > 0` nel `lookback_months`):

| Segmento | Condizione | Formula |
|----------|-----------|---------|
| Dormante | `active_months == 0` | `None` |
| Intermittente | `1 <= active_months < regular_threshold` | `total_qty / lookback_months * intermittent_factor` |
| Regolare | `regular_threshold <= active_months < continuous_threshold` | `total_qty / lookback_months * regular_factor` |
| Continuo | `active_months >= continuous_threshold` | percentile con rilevamento trend |

Per gli articoli **continui**, si rileva il trend confrontando la media degli ultimi 3 mesi
con la media del periodo intero:

- `trend_ratio = mean_3m / mean_full`
- se `trend_ratio > trend_ratio_threshold` → trend crescente → usa finestra 3m
- se `trend_ratio < 1 / trend_ratio_threshold` → trend decrescente → usa finestra 6m
- altrimenti → stabile → usa finestra `lookback_months` intera

Parametri configurabili:

| Parametro | Default | Significato |
|-----------|---------|-------------|
| `lookback_months` | `12` | Periodo di lookback totale |
| `continuous_threshold` | `8` | Soglia mesi per classificare "continuo" |
| `regular_threshold` | `3` | Soglia mesi per classificare "regolare" |
| `percentile_continuous` | `70` | Percentile applicato agli articoli continui |
| `zscore_threshold` | `2.0` | Soglia outlier z-score (solo articoli continui) |
| `regular_factor` | `1.2` | Moltiplicatore throughput per articoli regolari |
| `intermittent_factor` | `1.0` | Moltiplicatore throughput per articoli intermittenti |
| `trend_ratio_threshold` | `1.5` | Ratio 3m/full sopra cui scatta il trend crescente |
| `min_movements` | `3` | Soglia globale righe movimento |
| `rounding_scale` | `None` | Cifre decimali risultato finale |

---

### Registry e dispatch delle strategy

Le strategy ammesse sono definite in un registry chiuso nel codice:

```python
KNOWN_MONTHLY_BASE_STRATEGIES = [
    "monthly_stock_base_from_sales_v1",
    "monthly_stock_base_weighted_v2",
    "monthly_stock_base_segmented_v1",
]
```

Il routing avviene tramite `_MONTHLY_BASE_DISPATCH` in `queries.py`: una dict che mappa
`strategy_key → funzione`. La funzione riceve `monthly_sales`, `params`, `total_movements`
e restituisce `Decimal | None`.

Una strategy non presente nel dispatch fa fallback a `v1` (comportamento sicuro).

### Configurazione via UI admin

La configurazione delle strategy segue lo stesso pattern delle logiche proposal
(`AdminProposalLogicPage`):

- colonna sinistra: elenco delle strategy note con badge "Attiva"
- colonna destra: descrizione della strategy selezionata, textarea JSON per i parametri,
  pulsante "Imposta come strategy attiva"
- i parametri capacity (logica fissa `capacity_from_containers_v1`) hanno una sezione JSON separata

I parametri di default per ogni strategy sono precompilati dalla UI al momento della selezione
(da `stockLogicMeta.ts`). Il backend salva i parametri come JSON grezzo in
`core_stock_logic_config.monthly_base_params_json`.

---

## 7. Capacity

La V1 introduce:

- `capacity_calculated_qty`
- `capacity_override_qty`
- `capacity_effective_qty`

Regola:

- `capacity_effective_qty = capacity_override_qty` se presente
- altrimenti `capacity_effective_qty = capacity_calculated_qty`

Logica di setup:

- `capacity_calculated_qty` usa la logica fissa `capacity_from_containers_v1`
- `capacity_from_containers_v1` non e strategy-switchable
- i suoi parametri numerici restano comunque configurabili da configurazione interna V2
- i dati sorgente arrivano dai mirror V2 articolo/config, non da Easy diretto

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

### Orizzonte temporale stock

La componente stock-driven non deve reagire agli impegni cliente troppo lontani.

Serve quindi un primo `stock horizon` semplice.

Regola V1:

- il look-ahead stock sugli impegni e limitato a:
  - `effective_stock_months`

Forma concettuale:

- `stock_lookahead_months = effective_stock_months`
- `capped_commitments_qty`:
  - impegni con data consegna entro `today + stock_lookahead_months`

La componente stock-driven usa quindi una disponibilita dedicata di orizzonte:

```text
stock_horizon_availability_qty =
  inventory_qty
  - customer_set_aside_qty
  - capped_commitments_qty
  + incoming_supply_qty
```

Nota:

- il `customer_shortage_qty` continua a usare la logica customer-driven del planning
- il cap temporale vale solo per la componente `stock_replenishment_qty`

### Regola di trigger

Scatta un fabbisogno stock-driven se:

- `effective_gestione_scorte_attiva = true`
- `stock_horizon_availability_qty < trigger_stock_qty`

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
- `stock_replenishment_qty = max(target_stock_qty - max(stock_horizon_availability_qty, 0), 0)`
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
- `strategy_key`
- `params_snapshot`
- `computed_at`
- `algorithm_key`

## 11. Principio architetturale

La logica di scorta segue la stessa regola generale gia adottata in V2:

- i fact restano stabili
- le logiche che li interpretano sono sostituibili

Quindi:

- la selezione della strategy della base mensile
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
  - `gestione_scorte_attiva`
  - `stock_months`
  - `stock_trigger_months`
  - `capacity_override_qty`
- basata su:
  - `monthly_stock_base_qty`
  - `future_availability_qty`
- con candidato unico per articolo e breakdown interno:
  - shortage cliente
  - replenishment scorta
