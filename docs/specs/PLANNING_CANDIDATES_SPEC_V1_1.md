# PLANNING_CANDIDATES_SPEC_V1_1

## 1. Contesto

Il sistema dispone di:

- sincronizzazione dati da Easy in read-only
- fact canonici:
  - `inventory`
  - `commitments`
  - `customer_set_aside`
  - `availability`
- dati su produzioni attive e stato effettivo di completamento
- planning policy a livello famiglia e articolo
- refresh semantico backend

E gia presente una vista `criticita articoli` basata su `availability_qty < 0`, utile ma limitata come segnale immediato.

## 2. Obiettivo del modulo

Il modulo `Planning Candidates` ha lo scopo di:

> identificare e rappresentare i fabbisogni produttivi che meritano attenzione, tenendo conto di domanda, stock operativo e copertura gia in essere.

Nel baseline architetturale post-rebase il modulo deve anche distinguere in modo esplicito:

- esistenza del bisogno
- fattibilita del rilascio immediato

Produce una lista:

- spiegabile
- non duplicata
- utilizzabile come input del futuro modulo `Production Proposals`

## 3. Scope

### Il modulo FA

- identifica fabbisogni produttivi
- integra domanda cliente, stock operativo e produzioni attive
- distingue aggregazione e non aggregazione
- espone una reason esplicita per cui il candidate compare
- separa il bisogno eventuale dalla quantita lanciabile ora
- prepara il passaggio verso `Production Proposals`

### Il modulo NON FA

- non calcola la quantita produttiva finale
- non applica ancora lotti o multipli finali
- non schedula produzione
- non assegna risorse o macchine
- non gestisce ancora anomalie inventariali come modulo dedicato
- non decide da solo l'export o il rilascio proposal downstream

## 4. Posizionamento architetturale

Layer:

- `Core / Domain Logic`

Input:

- `articoli`
- `righe ordine cliente`
- `availability`
- `produzioni attive`
- planning policy effettive

Output:

- lista `Planning Candidates`

## 5. Concetti chiave

### 5.1 Planning Identity

Unita logica su cui si genera un candidate:

- `article` se il planning mode e `by_article`
- `customer_order_line` se il planning mode e `by_customer_order_line`

### 5.2 Unicita del candidate

Per ogni planning identity esiste al massimo un candidate principale.

Non sono ammessi duplicati logici per la stessa identity.

### 5.3 Planning Mode

Il comportamento e governato da:

- `planning_mode = by_article`
- `planning_mode = by_customer_order_line`

Il planning mode deriva dalla policy effettiva dell'articolo.

### 5.4 Reason esplicita

Ogni candidate deve esporre in modo esplicito:

- `reason_code`
- `reason_text`

per spiegare perche la riga e mostrata.

La reason non deve essere implicita nella sola presenza della riga.

## 6. Copertura da produzioni attive

Le produzioni attive sono considerate:

> copertura futura gia in corso

Non sono origine autonoma del candidate.

Nel planning:

- la supply in corso riduce la scopertura reale
- le produzioni completate devono essere escluse, anche via override `forza_completata`

## 7. Regola generale sulla giacenza negativa

### Principio

La giacenza negativa e un'anomalia inventariale, non un fabbisogno produttivo.

### Regola operativa

Per tutto il modulo `Planning Candidates` vale:

```text
stock_effective = max(stock_calculated, 0)
```

Uso:

- `stock_calculated` resta disponibile come dato tecnico
- `stock_effective` e l'unico valore da usare nella logica planning

### Conseguenza

La sola presenza di stock negativo:

- non genera automaticamente un candidate
- non compare come reason del candidate

La gestione dell'anomalia verra trattata in futuro nel modulo separato `Warnings`.

## 8. Quantita

Il candidate puo esporre livelli quantitativi diversi secondo il planning mode.

Nel modello post-rebase la quantita planning non deve piu avere un solo significato implicito.

Il modulo deve distinguere almeno:

- `required_qty_eventual`
- `release_qty_now_max`
- `release_status`

Nel primo slice implementativo del rebase questa distinzione viene resa pienamente nel solo ramo:

- `by_article`

Per il ramo:

- `by_customer_order_line`

il rebase quantitativo di `release now` resta esplicitamente rinviato per evitare duplicazione ambigua della stessa capienza articolo su piu righe cliente.

### Ramo by_article

Campi principali:

- `availability_qty`
- `incoming_supply_qty`
- `future_availability_qty`
- `required_qty_minimum`

Formula:

```text
future_availability_qty = availability_qty + incoming_supply_qty
```

Il candidate esiste quando la copertura futura resta negativa.

#### Distinzione `need vs release now`

Nel ramo `by_article` la V2 mantiene il breakdown oggi gia presente:

- `customer_shortage_qty`
- `stock_replenishment_qty`
- `required_qty_total`
- `primary_driver`

Ma il rebase architetturale introduce un secondo asse semantico, distinto dal solo need:

- `required_qty_eventual`
  - quanto manca rispetto al need/target futuro
- `release_qty_now_max`
  - quanta quantita e lanciabile ora senza violare la policy di capienza attuale
- `release_status`
  - `launchable_now`
  - `launchable_partially`
  - `blocked_by_capacity_now`

Regola concettuale:

```text
required_qty_eventual != release_qty_now_max
```

nei casi in cui il magazzino sia gia prossimo alla saturazione pur in presenza di un bisogno futuro reale.

La V4 legacy giustifica esplicitamente questa separazione con la logica:

```text
da_produrre = min(cap_residua, prod_a_scorta)
```

Quindi un candidate puo:

- esistere come bisogno reale
- ma risultare non lanciabile ora

senza che questo invalidi il candidate stesso.

#### Formula iniziale del rebase

Nuovi campi del ramo `by_article`:

- `required_qty_eventual`
- `capacity_headroom_now_qty`
- `release_qty_now_max`
- `release_status`

Formule iniziali:

```text
required_qty_eventual = required_qty_total
capacity_headroom_now_qty = max(capacity_effective_qty - inventory_qty, 0)
release_qty_now_max = min(required_qty_eventual, capacity_headroom_now_qty)
```

Regola importante:

- il confronto `release now` usa la giacenza fisica attuale (`inventory_qty`)
- non la sola `availability_qty`

per evitare che articoli gia quasi a capienza risultino lanciabili solo perche esistono impegni futuri.

Vocabolario iniziale di `release_status`:

- `launchable_now`
- `launchable_partially`
- `blocked_by_capacity_now`

Regole:

- `launchable_now`
  - `release_qty_now_max >= required_qty_eventual`
- `launchable_partially`
  - `0 < release_qty_now_max < required_qty_eventual`
- `blocked_by_capacity_now`
  - `release_qty_now_max = 0` e `required_qty_eventual > 0`

### Ramo by_customer_order_line

Campi principali:

- `line_open_demand_qty`
- `linked_incoming_supply_qty`
- `line_future_coverage_qty`
- `required_qty_minimum`

La supply e cercata solo sulle produzioni collegate alla stessa riga ordine cliente.

Nel ramo `by_customer_order_line` il rebase non elimina la semantica cliente-driven, ma richiede che la fattibilita di rilascio immediato resti distinta dal bisogno cliente netto, soprattutto nei casi di saturazione della capienza.

Nel primo slice implementativo:

- il ramo per-riga mantiene i campi attuali
- i nuovi campi `release now` possono restare assenti o `null`
- il modello quantitativo completo del per-riga verra trattato in uno slice dedicato

## 8B. Compatibilita di transizione

I campi attuali della V2 restano validi durante la transizione:

- `required_qty_minimum`
- `required_qty_total`
- `customer_shortage_qty`
- `stock_replenishment_qty`

Ma ogni nuovo sviluppo planning deve dichiarare esplicitamente se sta intervenendo su:

- `need detection`
- `release feasibility`
- oppure solo sul read model di presentazione

## 9. Regole di generazione

### 9.1 By Article

- aggregazione per articolo
- usa stock operativo e supply aggregata
- il candidate segnala una scopertura residua a livello codice
- il candidate puo avere due componenti logiche nello stesso record:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`

### 9.3 Customer Horizon

La componente customer-driven puo essere valutata anche rispetto a un primo orizzonte temporale
operativo semplice.

Configurazione iniziale prevista:

- `customer_horizon_days`

Semantica V1:

- basata solo su `data_consegna`
- senza usare ancora lead time, tempi ciclo o capacità

Il Core non deve perdere i candidate fuori orizzonte.

Deve invece poter esporre almeno:

- `is_within_customer_horizon`
- opzionalmente `customer_horizon_days_snapshot`

Regola concettuale:

```text
is_within_customer_horizon = delivery_date <= today + customer_horizon_days
```

Questo flag serve a:

- distinguere i fabbisogni cliente prossimi da quelli lontani
- abilitare filtri UI semplici senza rompere il modello base

### 9.2 By Customer Order Line

- un candidate per riga ordine cliente
- non usa aggregazione per codice
- la riga viene valutata contro la supply specificamente collegata

## 10. Regole di presentazione

### 10.1 By Article

La descrizione mostrata puo essere quella anagrafica articolo.

### 10.2 By Customer Order Line

La descrizione mostrata deve essere quella presente nell'ordine cliente.

Non va privilegiata la descrizione anagrafica articolo se diversa da quella commerciale/operativa della riga.

### 10.3 Misura

La vista deve esporre anche la misura in una colonna dedicata, per migliorare la leggibilita
operativa del candidate.

### 10.4 Reason

La vista deve mostrare sempre la ragione per cui la riga e presente.

Per i candidate `by_article` con piu componenti attive:

- la UI deve mostrare un badge sintetico per il driver primario
- la UI deve poter mostrare anche i motivi secondari attivi
- i casi misti devono quindi restare leggibili come:
  - `Cliente`
  - `Scorta`

### 10.5 Separazione operativa in UI

La separazione tra fabbisogno cliente e scorta deve avvenire in UI, non nel Core.

`Planning Candidates` resta un modulo unico.

La vista deve poter offrire almeno:

- `Tutti`
- `Solo fabbisogno cliente`
- `Solo scorta`

Regole minime dei filtri:

- `Solo fabbisogno cliente`:
  - `primary_driver = customer`
- `Solo scorta`:
  - `primary_driver = stock`

### 10.6 Precedenza di visualizzazione nei casi misti

Un candidate `by_article` puo avere entrambe le componenti attive:

- `customer_shortage_qty > 0`
- `stock_replenishment_qty > 0`

In questo caso:

- la riga deve restare unica
- la UI deve mostrare entrambe le ragioni / componenti quantitative
- la classificazione primaria della riga deve essere:
  - `customer`

Regola di precedenza:

1. se `customer_shortage_qty > 0`
   - `primary_driver = customer`
2. altrimenti, se `stock_replenishment_qty > 0`
   - `primary_driver = stock`

Conseguenza:

- un articolo misto compare nella scheda `customer`
- non deve comparire anche nella scheda `stock`

La vista deve anche poter filtrare i candidate cliente per orizzonte temporale:

- `solo entro customer horizon`

### 10.7 Data richiesta in tabella

Per aumentare la leggibilita operativa, la vista `Planning Candidates` deve esporre anche una
data richiesta, ma con semantica diversa secondo il planning mode.

Regola:

- nel ramo `by_customer_order_line`
  - mostrare la `data_consegna_richiesta` della riga ordine cliente
- nel ramo `by_article`
  - mostrare solo la `prima data richiesta cliente`
  - il campo e valorizzato solo se esiste componente customer
  - nei casi `stock-only` il campo resta vuoto / `null`

Vincolo:

- non deve essere mostrata una data inventata per candidate puramente stock-driven
- la futura semantica `prima data scoperta` resta fuori scope per questa V1

### 10.8 Descrizione ordine completa

Nel ramo `by_customer_order_line` la descrizione mostrata non deve fermarsi al solo segmento
principale della riga se il Core ordini ha gia aggregato anche righe descrittive collegate.

Regola:

- il Core planning deve esporre una `full_order_line_description`
- la descrizione completa deriva da:
  - `article_description_segment`
  - `description_lines`

La UI deve usare questa descrizione completa come testo primario del candidate per-riga.

### 10.8.1 Modello descrittivo unificato

Per evitare che i due rami del planning usino modelli descrittivi incompatibili, il Core deve
convergere verso un contratto unico:

- `description_parts: list[str]`
- `display_description: str`

Regola di costruzione:

- `by_customer_order_line`
  - `description_parts = [article_description_segment, ...description_lines]`
- `by_article`
  - `description_parts = [descrizione_1, descrizione_2]`

In entrambi i casi:

- i segmenti vuoti vengono rimossi
- l'ordine dei segmenti viene preservato
- `display_description` deriva da `description_parts`
- fallback finale:
  - `article_code` se `description_parts` e vuota

`by_customer_order_line` resta il riferimento semantico piu ricco e guida la forma del modello
canonico.

### 10.9 Destinazione richiesta

La vista puo esporre anche la destinazione associata alla richiesta, ma con semantica esplicita.

Regola:

- nel ramo `by_customer_order_line`
  - la destinazione deriva dalla riga ordine cliente
  - il testo mostrato segue il comportamento:
    - `nickname_destinazione`, se presente
    - altrimenti label di default della destinazione
- nel ramo `by_article`
  - la destinazione e valorizzabile solo se e associabile in modo non ambiguo alla richiesta
    cliente che guida la data mostrata
  - se la richiesta cliente rilevante non e univoca, il campo puo mostrare `Multiple`
  - nei casi `stock-only`, il campo resta vuoto / `null`

### 10.10 Famiglia e motivi come badge

Per aumentare la leggibilita:

- `famiglia_label` deve poter essere resa come badge visivo
- `reason_code` / `primary_driver` devono poter essere resi come badge sintetici

La palette dei badge famiglia deve essere centralizzata e avere fallback neutro.

### 10.11 Warning articolo nella vista planning

Poiche il ramo `by_article` puo ora includere la componente stock-driven, la vista planning deve
rendere visibili anche gli errori di configurazione articolo che impattano direttamente la lettura
del candidate.

Regola:

- `Planning Candidates` puo esporre una colonna `warnings`
- la colonna mostra gli warning attivi collegati all'articolo del candidate
- gli warning devono essere letti dal modulo `Warnings`, non ricalcolati nella query planning
- la lista warning mostrata deve rispettare:
  - `visible_to_areas`
  - area corrente dell'utente

Primo warning in scope:

- `INVALID_STOCK_CAPACITY`

La UI deve poter mostrare badge warning sintetici, mantenendo la possibilita di estensione a tipi
warning futuri.

### 10.12 Quick edit articolo dalla vista planning

Per ridurre il tempo tra rilevazione del problema e correzione, la vista planning puo offrire una
quick action di configurazione articolo.

Regola:

- vicino al codice articolo puo esistere un'azione rapida, per esempio un pulsante `ingranaggio`
- l'azione apre un modal di configurazione articolo
- il modal non introduce un nuovo dominio di configurazione
- il modal deve riusare i contract gia esistenti della surface `articoli`

Perimetro minimo del modal:

- famiglia articolo
- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`
- `capacity_override_qty`

Vincolo:

- il modal e un entry point rapido verso configurazioni gia esistenti
- non deve divergere semanticamente dalla surface `articoli`

## 11. Entity Model

Shape logica minima:

```text
PlanningCandidate

candidate_id
planning_mode
planning_key

article_code
article_description
family_code
family_label

reason_code
reason_text

required_qty_minimum
computed_at
```

Semantica di `required_qty_minimum` nel ramo `by_article`:

- se `primary_driver = customer`
  - `required_qty_minimum = customer_shortage_qty`
- se `primary_driver = stock`
  - `required_qty_minimum = stock_replenishment_qty`

Quindi, nel caso `stock-only`, il fabbisogno minimo coincide con:

```text
max(target_stock_qty - max(stock_horizon_availability_qty, 0), 0)
```

Campi ramo `by_article`:

```text
description_parts
display_description
availability_qty
incoming_supply_qty
future_availability_qty
customer_shortage_qty
stock_replenishment_qty
required_qty_total
primary_driver
is_within_customer_horizon
earliest_customer_delivery_date
requested_destination_display
active_warnings
```

Campi ramo `by_customer_order_line`:

```text
description_parts
display_description
order_reference
line_reference
order_line_description
full_order_line_description
measure
requested_delivery_date
requested_destination_display
active_warnings
line_open_demand_qty
linked_incoming_supply_qty
line_future_coverage_qty
```

## 12. Relazione con sistema attuale

`Planning Candidates`:

- evolve la logica di criticita
- introduce un livello decisionale superiore rispetto ai soli fact quantitativi
- resta compatibile con i fact canonici esistenti
- deve chiudersi bene prima dell'apertura del modulo `Production Proposals`

## 13. Relazione con moduli futuri

Output -> input per:

- `Production Proposals`
- futuri moduli di scheduling

Nota di confine:

- `Planning Candidates` rileva il bisogno
- `Production Proposal` trasforma il bisogno in decisione operativa persistente
- la specifica del modulo proposal vive separatamente in `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`

## 14. Principio guida finale

> `Planning Candidates` rappresenta la pressione produttiva reale, considerando domanda cliente, stock operativo clampato a zero e copertura gia in essere, senza confondere le anomalie inventariali con il bisogno produttivo.
