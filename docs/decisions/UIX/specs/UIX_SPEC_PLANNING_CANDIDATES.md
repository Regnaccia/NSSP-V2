# UIX_SPEC_PLANNING_CANDIDATES - Vista operativa Planning Candidates

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-10

## Purpose

Documentare la surface UI di `Planning Candidates`, nata nella V1 ridotta e poi evoluta alla V2 con branching reale, coerente con:

- `DL-ARCH-V2-025`
- `DL-ARCH-V2-026`
- `DL-ARCH-V2-027`
- il completamento di `TASK-V2-062`
- il completamento di `TASK-V2-064`
- il completamento di `TASK-V2-071`
- il completamento di `TASK-V2-072`

La spec descrive la surface operativa di planning nello stato attuale, non l'intero modulo futuro.

## Related Documents

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md`
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`
- `docs/task/TASK-V2-062-core-planning-candidates-v1.md`
- `docs/task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md`
- `docs/task/TASK-V2-064-core-effective-planning-policy-articoli.md`
- `docs/task/TASK-V2-071-core-planning-candidates-v2-branching.md`
- `docs/task/TASK-V2-072-ui-planning-candidates-v2-branching.md`

## Variant

- pattern adottato: `1 colonna operativa`

Motivazione:

- non esiste ancora un dettaglio naturale a destra paragonabile ad `articoli`
- la prima esigenza operativa resta scanning rapido di una lista planning-oriented
- la vista deve ora poter ospitare sia candidate aggregati per articolo sia candidate per riga ordine

## Surface Goal

La vista deve rispondere a una domanda semplice:

> quali articoli richiedono ancora attenzione produttiva anche dopo la supply gia in corso?

La surface non deve ancora spiegare:

- quando la supply arrivera
- come schedularla
- quale lotto finale produrre

## Data Semantics

La vista consuma il read model Core `Planning Candidates` nello stato attuale V2.

Campi quantitativi minimi attesi:

- campi comuni:
  - `article_code`
  - `display_label`
  - `famiglia_label`
  - `planning_mode`
  - `required_qty_minimum`
- ramo `by_article`:
  - `customer_open_demand_qty`
  - `availability_qty`
  - `incoming_supply_qty`
  - `future_availability_qty`
- ramo `by_customer_order_line`:
  - `order_reference`
  - `line_reference`
  - `line_open_demand_qty`
  - `linked_incoming_supply_qty`
  - `line_future_coverage_qty`

Campi di policy effettiva attesi dopo `TASK-V2-064`:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`

## Column Model

### Vista unica - Tabella operativa

La schermata e una tabella piena larghezza con toolbar superiore.

Contiene:

- titolo della vista
- conteggio totale candidate
- filtri
- azione `Aggiorna`
- tabella dei candidate

## Toolbar

La toolbar V1 deve restare minima.

### Ricerca

Ricerca per:

- `article_code`
- opzionalmente `article_description`

La ricerca e operativa e non deve introdurre ancora comportamenti complessi o parsing speciale.

### Filtro famiglia

Filtro opzionale per `family_name` / `famiglia articolo`.

Serve per:

- restringere il focus operativo
- supportare verifica e debug

### Toggle `solo_in_produzione`

La V1 deve poter filtrare i candidate usando:

- `effective_considera_in_produzione = true`

Default:

- attivo

Motivazione:

- il planning operativo V1 deve focalizzarsi per default sugli articoli realmente nel perimetro di produzione/planning
- il toggle resta utile per debug o dati ancora incompleti

## Table Columns

Ordine consigliato delle colonne nello stato attuale:

1. `Codice`
2. `Descrizione`
3. `Famiglia`
4. `Mode`
5. `Ordine / Riga`
6. `Domanda`
7. `Dispon. attuale`
8. `Supply`
9. `Copertura`
10. `Fabbisogno minimo`

## Sorting

Ordinamento iniziale consigliato:

- `required_qty_minimum` decrescente

Alternativa ammessa:

- `future_availability_qty` crescente

Obiettivo:

- mostrare prima gli articoli con maggiore scopertura residua

## Visual Semantics

La vista deve essere leggibile ma non trasformarsi ancora in dashboard.

Regole minime:

- `future_availability_qty` negativa evidenziata con semantica critica
- `required_qty_minimum` visibile come dato principale di azione
- evitare badge o colori ridondanti su tutte le colonne

## Refresh Behavior

La vista non deve introdurre una chain tecnica locale.

Regola:

- il pulsante `Aggiorna` deve riusare un refresh semantico backend esistente o un refresh semantico dedicato al modulo
- la UI non deve ricostruire a mano le dipendenze

La scelta finale del refresh non e definita in questa spec, ma la surface deve restare coerente con `DL-ARCH-V2-022`.

## Empty States

### Nessun candidate

Messaggio guida:

- nessun articolo richiede nuova attenzione produttiva nel perimetro corrente

### Nessun risultato filtrato

Messaggio guida:

- nessun candidate corrisponde ai filtri attivi

## Out of Scope

La V1 UI non include ancora:

- pannello dettaglio a destra
- score o ranking composito
- planning horizon
- stati multipli tipo `monitor`
- raggruppamenti avanzati
- drill-down per riga ordine
- editing di policy dalla stessa vista

## Notes

- La surface resta intenzionalmente piu vicina a `criticita` che a un planner completo.
- Lo stato attuale include gia il branching reale `by_article` / `by_customer_order_line`.
- Le future evoluzioni potranno introdurre:
  - policy di aggregazione piu ricche
  - slice temporali
  - scoring
  - detail panel

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
