# Planning And Stock Rules

## Scopo

Questa guida raccoglie in un solo punto le regole operative oggi stabili su:

- `Planning Candidates`
- stock policy V1
- warning collegati alla stock policy

Non sostituisce:

- le `spec`
- i `DL`

Serve come riferimento rapido quando si lavora su Core, UI o task futuri.

## 1. Planning Modes

`Planning Candidates` supporta due modalita esplicite:

- `by_article`
- `by_customer_order_line`

Regola:

- `by_article` = ragionamento aggregato per articolo
- `by_customer_order_line` = ragionamento per singola riga ordine cliente

## 2. Giacenza Negativa

La giacenza negativa e un'anomalia inventariale, non un fabbisogno produttivo.

Regola planning:

```text
stock_effective = max(stock_calculated, 0)
```

Quindi:

- lo stock negativo non genera da solo un candidate
- lo stock negativo non deve essere usato come reason del candidate
- le anomalie stanno nel modulo `Warnings`

## 3. Candidate Unico Per Articolo

Nel ramo `by_article` non devono nascere due candidate distinti per lo stesso articolo.

Il Core resta unico e usa un solo candidate con breakdown interno:

- `customer_shortage_qty`
- `stock_replenishment_qty`
- `required_qty_total`

Formule V1:

```text
customer_shortage_qty = max(-future_availability_qty, 0)
stock_replenishment_qty = max(target_stock_qty - max(stock_horizon_availability_qty, 0), 0)
required_qty_total = customer_shortage_qty + stock_replenishment_qty
```

## 3.1 Need vs Release Now

Nel rebase architetturale il ramo `by_article` distingue due semantiche quantitative diverse:

- `required_qty_eventual`
  - quanto manca rispetto al bisogno futuro
- `release_qty_now_max`
  - quanto e lanciabile ora senza violare la capienza attuale

Primo profilo del rebase:

```text
required_qty_eventual = required_qty_total
capacity_headroom_now_qty = max(capacity_effective_qty - inventory_qty, 0)
release_qty_now_max = min(required_qty_eventual, capacity_headroom_now_qty)
```

Stati iniziali:

- `launchable_now`
- `launchable_partially`
- `blocked_by_capacity_now`

Regola fondamentale:

- il need non sparisce se `release_qty_now_max = 0`
- il candidate resta visibile come bisogno reale, ma non va trattato come rilascio immediato disponibile

## 4. Separazione Cliente / Scorta

La separazione tra fabbisogno cliente e scorta avviene in UI, non nel Core.

La vista `Planning Candidates` deve poter offrire almeno:

- `Tutti`
- `Solo fabbisogno cliente`
- `Solo scorta`

Regole minime:

- `Solo fabbisogno cliente`:
  - `primary_driver = customer`
- `Solo scorta`:
  - `primary_driver = stock`

## 4.1 Casi Misti

Un articolo `by_article` puo avere entrambe le componenti attive:

- `customer_shortage_qty > 0`
- `stock_replenishment_qty > 0`

Regola:

- la riga resta unica
- la UI mostra entrambe le componenti
- la classificazione primaria deve essere `customer`

Precedenza:

1. `customer`
2. `stock`

Quindi:

- un candidato misto compare nella scheda `customer`
- non compare anche nella scheda `stock`

## 4.2 Fabbisogno Minimo

`required_qty_minimum` deve restare coerente con il driver primario della riga.

Regola nel ramo `by_article`:

- se `primary_driver = customer`
  - `required_qty_minimum = customer_shortage_qty`
- se `primary_driver = stock`
  - `required_qty_minimum = stock_replenishment_qty`

Quindi, nel caso `stock-only`, il fabbisogno minimo coincide con il replenishment scorta.

## 4.3 Data richiesta in tabella

La UI `Planning Candidates` puo esporre una data richiesta, ma senza mescolare semantiche diverse.

Regola:

- `by_customer_order_line`
  - mostra `requested_delivery_date`
- `by_article`
  - mostra `earliest_customer_delivery_date` solo se esiste componente customer
- `stock-only`
  - non mostra una data inventata

La futura semantica `prima data scoperta` resta fuori scope per questa V1.

## 4.4 Descrizione e destinazione della richiesta

Nel ramo `by_customer_order_line` la UI planning non deve usare solo il primo segmento descrittivo
della riga.

Regole:

- il target canonico e:
  - `description_parts`
  - `display_description`
- `by_customer_order_line` e il riferimento semantico del modello
- nel ramo per-riga:
  - `description_parts = [article_description_segment, ...description_lines]`
- nel ramo aggregato:
  - `description_parts = [descrizione_1, descrizione_2]`
- `display_description` deriva da `description_parts`
- la destinazione richiesta usa:
  - `nickname_destinazione`, se presente
  - altrimenti la label di default della destinazione

Nel ramo `by_article`:

- la destinazione puo essere mostrata solo se associabile in modo non ambiguo alla richiesta
  cliente che guida la data mostrata
- se il mapping non e univoco:
  - `Multiple`
- nei casi `stock-only`:
  - nessuna destinazione inventata

## 4.5 Badge di leggibilita

La UI planning puo migliorare la leggibilita con badge sintetici, senza cambiare il modello Core.

Regole:

- `famiglia_label` puo essere resa come badge con palette centralizzata
- `primary_driver` e i motivi attivi possono essere resi come badge sintetici
- i casi misti mostrano badge multipli (`Cliente`, `Scorta`) ma restano una sola riga
- `misura` va esposta in una colonna dedicata

## 5. Stock Policy V1

La stock policy V1 vale solo se entrambe le condizioni sono vere:

- `planning_mode = by_article`
- `effective_gestione_scorte_attiva = true`

Quindi:

- `by_article` da solo non basta
- la gestione scorte e una policy esplicita separata

## 6. Configurazione Stock

Default famiglia:

- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`

Override articolo:

- `override_gestione_scorte_attiva`
- `override_stock_months`
- `override_stock_trigger_months`
- `capacity_override_qty`

Valori effettivi attesi:

- `effective_gestione_scorte_attiva`
- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`

## 7. Monthly Stock Base

La base mensile di scorta e:

- `monthly_stock_base_qty`

Regole V1:

- sorgente: mirror interno `sync_mag_reale`
- nessuna lettura diretta da Easy nella logica Core
- strategy selezionabile via `strategy_key`
- parametri numerici configurabili da configurazione interna

Strategia iniziale:

- `monthly_stock_base_from_sales_v1`

Profilo V1:

- finestre multiple:
  - `12`
  - `6`
  - `3` mesi
- percentile configurabile
- filtro outlier z-score configurabile
- `min_movements`
- `rounding_scale`
- output `None` quando il dato e incalcolabile

## 8. Capacity

Metriche:

- `capacity_calculated_qty`
- `capacity_override_qty`
- `capacity_effective_qty`

Regola:

```text
capacity_effective_qty = capacity_override_qty if present else capacity_calculated_qty
```

La `capacity`:

- e proprieta dell'articolo
- non ha default di famiglia

Logica V1:

- `capacity_from_containers_v1`
- fissa, non strategy-switchable
- riallineata alla formula legacy
- dipende da parametri admin, in particolare `max_container_weight_kg`

## 9. Stock Horizon

La componente scorta non deve reagire a domanda troppo lontana.

Serve quindi un `stock horizon`.

Regola V1:

- il look-ahead stock sugli impegni e limitato a:
  - `effective_stock_months`

La componente stock-driven usa:

- `stock_horizon_availability_qty`

e non la stessa quantita customer-driven senza cap temporale.

## 10. Customer Horizon

Il customer-driven puo introdurre un primo orizzonte semplice separato dalla stock policy.

Configurazione iniziale prevista:

- `customer_horizon_days`

Semantica V1:

- basata solo su `data_consegna`
- nessun lead time
- nessun tempo ciclo
- nessuna capacita

Il Core non deve scartare i candidate fuori orizzonte.

Deve invece poter esporre:

- `is_within_customer_horizon`

## 11. Warnings Collegati

I warning oggi rilevanti per planning/stock sono:

- `NEGATIVE_STOCK`
- `INVALID_STOCK_CAPACITY`

Regole:

- i warning sono canonici e non duplicati per reparto
- la visibilita usa `visible_to_areas`
- `admin` vede il quadro trasversale completo

`INVALID_STOCK_CAPACITY` ha senso solo nel perimetro stock policy, quindi concettualmente richiede:

- `planning_mode = by_article`
- `effective_gestione_scorte_attiva = true`
- `capacity_effective_qty` invalida o assente

### 11.1 Integrazione nella vista planning

La vista `Planning Candidates` puo mostrare warning attivi dell'articolo, ma senza duplicare la
logica del modulo `Warnings`.

Regole:

- i warning in planning sono un enrichment di lettura
- la colonna `Warnings` consuma warning canonici filtrati per `visible_to_areas`
- il primo warning rilevante e:
  - `INVALID_STOCK_CAPACITY`
- il quick fix da planning deve riusare la configurazione articolo gia esistente

## 12. Confini Importanti

`Planning Candidates`:

- rileva il bisogno
- non decide ancora la proposta produttiva finale

`Warnings`:

- espone anomalie di dato o configurazione
- non sostituisce il planning

`Production Proposals`:

- resta il modulo futuro che trasformera il bisogno in decisione operativa persistente

## References

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
