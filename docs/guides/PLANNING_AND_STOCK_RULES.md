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
