# UIX_SPEC_PLANNING_CANDIDATES - Vista operativa Planning Candidates

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-17

## Purpose

Documentare la surface UI di `Planning Candidates`, nata nella V1 ridotta e poi evoluta alla V2 con branching reale, coerente con:

- `DL-ARCH-V2-025`
- `DL-ARCH-V2-026`
- `DL-ARCH-V2-027`
- il completamento di `TASK-V2-062`
- il completamento di `TASK-V2-064`
- il completamento di `TASK-V2-071`
- il completamento di `TASK-V2-072`

La spec descrive la surface operativa di planning nello stato attuale e congela il contratto UX di:

- colonna sinistra
- colonna centrale
- primo slice della colonna destra per la scheda `Planning / Scorte`

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

- stato corrente implementato: `1 colonna operativa`
- target UX post-rebase: `3 colonne`

Motivazione target:

- la surface planning deve diventare il workspace operativo primario
- il triage dei candidate va separato dal dettaglio e dal pannello proposal
- il pattern resta coerente con l'impostazione multi-colonna gia adottata dal resto del sistema

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

### Stato corrente - Tabella operativa piena larghezza

La schermata oggi implementata e una tabella piena larghezza con toolbar superiore.

Contiene:

- titolo della vista
- conteggio totale candidate
- filtri
- azione `Aggiorna`
- tabella dei candidate

### Target rebase - Unified Planning Workspace

Target surface:

1. colonna sinistra
   - inbox sintetica dei candidate
2. colonna centrale
   - dettaglio del candidate selezionato
3. colonna destra
   - pannello proposal contestuale

Regola di selezione:

- quando l'utente seleziona un candidate nella colonna sinistra
  - si aggiornano subito:
    - colonna centrale
    - colonna destra
- la colonna destra non deve richiedere un'azione secondaria per apparire
- se nessun candidate e selezionato:
  - la colonna destra puo mostrare uno stato vuoto / placeholder

Questa spec congela:

- colonna sinistra
- colonna centrale
- primo slice della colonna destra:
  - scheda `Planning / Scorte`

Il dettaglio completo del pannello proposal della colonna destra resta ancora aperto.

## Left Column Contract

### Ruolo

La colonna sinistra e una inbox sintetica operativa.

Serve a:

- riconoscere rapidamente il caso
- ordinare e prioritizzare il lavoro
- capire stato di rilascio, stato proposta e stato operativo
- scegliere quale candidate aprire nel dettaglio

Non serve a:

- spiegare tutto il breakdown quantitativo
- mostrare la diagnostica completa
- sostituire il dettaglio centrale

### Campi visibili

Ogni riga sintetica della colonna sinistra deve mostrare:

- `cliente_scope_label`
  - `Cliente`
  - `Magazzino`
  - `Cliente + Magazzino`
- `article_code`
- `display_description`
- `measure`
- `requested_delivery_date`
  - solo se esiste componente customer
- `release_status`
- `proposal_status`
- `workflow_status`
- `priority_score`
  - placeholder V1, anche non ancora calcolato
- segnale warning minimo:
  - triangolo rosso se e presente almeno un warning

### Gerarchia interna della card

La card della colonna sinistra deve seguire questo ordine visivo:

1. riga 1
   - `cliente_scope_label`
   - triangolo warning allineato in alto a destra della card, se presente almeno un warning
2. riga 2
   - `article_code`
   - `measure`
   - stesso peso visivo
3. riga 3
   - `display_description`
4. riga 4
   - `requested_destination_display + requested_delivery_date`
   - solo se esiste componente customer
5. riga 5
   - badge stati:
     - `proposal_status`
     - `workflow_status`
     - `release_status`
6. `priority_score`
   - mostrato come valore sintetico dedicato della card
   - visivamente separato dai badge di stato

Quantita sintetica:

- `required_qty_eventual`
- allineata a destra nella card

Priorita sintetica:

- `priority_score`
- deve essere visibile nella card sinistra
- non deve sostituire `required_qty_eventual`
- il formato iniziale puo essere:
  - solo valore numerico
  - oppure valore numerico + label/badge secondario in evoluzioni successive

Regole:

- `requested_destination_display + requested_delivery_date` non compare nei casi `stock-only`
- il warning resta solo un segnale minimo visivo, non un blocco descrittivo
- `article_code` e `measure` non hanno gerarchia tipografica diversa

### Campi esclusi

La colonna sinistra non deve mostrare:

- dettaglio warning
- `logic hint`
- breakdown quantitativi completi
- `proposal_fallback_reason`
- `note` export
- dettagli ordine estesi

Questi dati appartengono alla colonna centrale o destra.

### Sorting iniziale della inbox

La colonna sinistra deve supportare sorting per priorita.

Contratto minimo V1:

- sorting disponibile per `priority_score`
- ordinamento consigliato iniziale:
  - `priority_score desc`

Sorting secondari gia ammessi:

- `article_code`
- `requested_delivery_date`

Regola:

- il sorting per priorita deve essere disponibile senza alterare il significato del candidate
- il sorting resta una funzione di inbox/workspace, non una regola di dominio

### Stato proposta

`proposal_status` e il badge principale.

Vocabolario iniziale:

- `Error`
- `Need review`
- `Valid for export`

Semantica:

- `Error`
  - proposta non esportabile per errore bloccante
- `Need review`
  - proposta costruita ma non ancora considerata pronta
- `Valid for export`
  - proposta pronta per entrare in export batch

### Stato operativo

`workflow_status` e il badge secondario.

Vocabolario iniziale:

- `Inattivo`
- `Preso in carico`
- `In batch export`

Semantica:

- `Inattivo`
  - candidate presente ma non ancora preso in carico nel workspace
- `Preso in carico`
  - candidate attualmente lavorato o gia aperto nel pannello operativo
- `In batch export`
  - candidate gia inserito nel batch corrente

### Gerarchia visiva

Ordine di lettura richiesto:

1. `proposal_status`
2. `workflow_status`
3. `release_status`
4. identificazione del caso:
   - `cliente_scope_label`
   - `article_code`
   - `display_description`
   - `measure`
   - `requested_delivery_date`
5. warning signal minimo
6. `priority_score`

Regole:

- `proposal_status` ha il peso visivo piu forte
- `workflow_status` e secondario ma sempre visibile
- `release_status` resta un segnale operativo del candidate, non sostituisce gli altri due stati
- il warning non diventa badge descrittivo: e solo un alert visivo minimo

## Center Column Contract

### Ruolo

La colonna centrale e la colonna di comprensione e validazione del candidate.

Serve a:

- spiegare perche il candidate esiste
- rendere leggibile il rapporto tra bisogno e rilascio
- mostrare il contesto cliente / ordine quando rilevante
- mostrare il contesto stock / capienza quando rilevante
- spiegare il triangolo warning mostrato nella colonna sinistra

Non serve a:

- editare la proposta
- mostrare azioni di export
- anticipare la proposal con blocchi di configurazione

### Blocchi

La colonna centrale e composta dai seguenti blocchi:

1. `Identita`
2. `Cliente / Ordine`
3. `Need vs Release`
4. `Stock / Capienza`
5. `Parametri di calcolo`
6. `Motivo`
7. `Warnings`
8. `Priority`

### 1. Identita

Sempre visibile.

Campi:

- `article_code`
- `display_description`
- `measure`
- `family_label`

Regola:

- il blocco `Identita` non ripete il `cliente_scope_label`
- la gerarchia visiva interna del blocco e:
  1. `article_code - measure`
  2. `display_description`
  3. triangolo warning in alto a destra se presente almeno un warning

### 2. Cliente / Ordine

Sempre visibile nel ramo:

- `by_article`

Visibile anche nel ramo:

- `by_customer_order_line`

Campi:

- `cliente_scope_label`
- `requested_delivery_date`
- `requested_destination_display`
- `order_reference`
- `line_reference`

Nel ramo `by_article`, il blocco deve anche poter mostrare una sottosezione:

- `Ordini aperti`

Regola:

- nel caso `by_customer_order_line` il blocco non ripete `full_order_line_description`, gia resa in `display_description` nel blocco `Identita`
- nel ramo `by_article`, la sottosezione `Ordini aperti` mostra tutte le righe cliente ancora aperte dell'articolo
- nei casi `stock-only`, il blocco resta visibile proprio per esporre gli impegni cliente presenti e futuri
- in `stock-only`, i campi sintetici del blocco possono essere vuoti o ridotti, ma la sottosezione `Ordini aperti` resta disponibile quando esistono righe aperte

### Sottosezione `Ordini aperti` - ramo `by_article`

Scopo:

- rendere visibile la distribuzione temporale reale degli impegni cliente
- distinguere gli ordini che ricadono dentro o fuori l'`Orizzonte cliente`

Perimetro:

- solo righe aperte
- `open_qty` calcolata tenendo conto della quantita appartata

Formula minima:

```text
open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```

Campi minimi per riga:

- `requested_delivery_date`
- `order_reference`
- `requested_destination_display`
- `open_qty`

Distinzione visiva obbligatoria:

- `entro orizzonte`
- `oltre orizzonte`

Regole:

- la distinzione usa il valore attuale di `customer_horizon_days` del workspace
- gli ordini sono ordinati per `requested_delivery_date` crescente
- la sottosezione non compare nel ramo `by_customer_order_line`
- la sottosezione puo comparire anche nei casi `stock-only`, per rendere leggibile la distribuzione temporale degli impegni cliente pur in assenza di shortage cliente entro orizzonte

### 3. Need vs Release

Sempre visibile nel ramo `by_article`.

Versione ridotta nel ramo `by_customer_order_line`.

Campi nel ramo `by_article`:

- `customer_shortage_qty`
- `stock_replenishment_qty`
- `required_qty_eventual`
- `release_qty_now_max`
- `release_status`

Campi nel ramo `by_customer_order_line`:

- `line_open_demand_qty`
- `linked_incoming_supply_qty`
- `line_future_coverage_qty`
- `required_qty_minimum`

Regole:

- questo e il blocco quantitativo principale della colonna centrale
- non deve duplicare altri numeri secondari non necessari
- nel ramo `by_customer_order_line` non si inventano campi `release now` non ancora supportati

### 4. Stock / Capienza

Sempre visibile nel ramo `by_article`.

Nascosto nel ramo `by_customer_order_line`.

Campi primari:

- `stock_effective_qty`
- `availability_qty`
- `capacity_effective_qty`
- `capacity_headroom_now_qty`

Campi secondari ammessi solo se gia disponibili senza rumore aggiuntivo:

- `future_availability_qty`
- `incoming_supply_qty`

Regole:

- i campi primari sono il contratto minimo obbligatorio
- i campi secondari non devono oscurare i primari
- nel blocco UI non si deve mostrare la giacenza raw negativa
- il valore da mostrare e la giacenza effettiva di planning:
  - `stock_effective_qty = max(inventory_qty, 0)`

### 5. Parametri di calcolo

Sempre visibile nel ramo `by_article`.

Non mostrato nel ramo `by_customer_order_line` nel primo slice.

Ruolo:

- spiegare con quali parametri effettivi il candidate e stato calcolato
- rendere leggibile la provenienza dei valori configurativi
- offrire una CTA verso la configurazione della colonna destra

Campi read-only:

- `effective_gestione_scorte_attiva`
- `effective_stock_months`
- `effective_stock_trigger_months`
- `capacity_effective_qty`
- `monthly_stock_base_qty`
- `target_stock_qty`
- `trigger_stock_qty`
- `customer_horizon_days`
  - come valore attuale del filtro/workspace
- provenienza dei parametri, almeno per:
  - `effective_gestione_scorte_attiva`
  - `effective_stock_months`
  - `effective_stock_trigger_months`
  - `capacity_effective_qty`

Vocabolario provenienza:

- `default famiglia`
- `override articolo`
- `calcolato`
- `workspace`

CTA obbligatoria:

- `Override`

Effetto della CTA:

- non apre un modal
- non apre la colonna destra da zero
- cambia il focus / la scheda attiva della colonna destra gia visibile

Regole:

- il blocco resta read-only
- non introduce campi editabili nella colonna centrale
- `customer_horizon_days` e mostrato come parametro operativo del workspace, non come configurazione persistente articolo

### 6. Motivo

Sempre visibile.

Campi:

- `reason_code`
- `reason_text`
- `primary_driver`

Regola:

- `reason_text` e `primary_driver` sono i segnali principali per l'operatore
- `reason_code` puo restare piu tecnico o secondario

### 7. Warnings

Sempre visibile.

Rendering:

- se non esistono warning:
  - stato sintetico `Nessun warning`
- se esistono warning:
  - lista leggibile degli warning attivi

Campi:

- `active_warning_codes`
- `active_warnings`

Regola:

- questo blocco spiega il triangolo warning mostrato nella colonna sinistra
- il dettaglio warning vive qui, non nella inbox sintetica

### 8. Priority

Visibile quando il candidate espone `priority_score`.

Ruolo:

- spiegare il punteggio di priorita
- evitare che `priority_score` sia percepito come numero opaco
- rendere leggibili componenti e summary del ranking planning

Campi minimi target:

- `priority_score`
- `priority_band`
- `priority_reason_summary`
- `priority_score_policy_key`

Componenti target:

- `time_urgency`
- `customer_pressure`
- `stock_pressure`
- `release_penalty`
- `warning_penalty`

Regole:

- il blocco resta read-only
- le componenti positive devono essere mostrate come contributi
- le penalita devono essere rese chiaramente come componenti negative
- il blocco non introduce editing o configurazione del punteggio nella colonna centrale

Strategia di rollout:

- primo slice ammesso:
  - `priority_score`
  - `priority_reason_summary`
- slice completo target:
  - score totale
  - `priority_band`
  - `priority_score_policy_key`
  - dettaglio componenti

## Right Column Contract - First Slice

### Ruolo

La colonna destra e il pannello di azione e configurazione.

Nel primo slice chiuso da questa spec viene congelata solo la scheda:

- `Planning / Scorte`

Le schede proposal ed export restano fuori da questo perimetro.

### Scheda `Planning / Scorte`

Scopo:

- permettere override rapidi dei parametri configurabili che influenzano il planning
- restando coerente con i contract gia esistenti della surface `articoli`

Campi editabili:

- `planning_mode`
- `gestione_scorte_attiva`
- `stock_months`
- `stock_trigger_months`
- `capacity_override_qty`

Campi esclusi in questo slice:

- `monthly_base_strategy_key`
- parametri numerici interni della strategy stock
- qualsiasi parametro proposal:
  - `proposal_logic_key`
  - `proposal_logic_article_params`
  - `raw_bar_length_mm`
  - `bar_multiple`

Regole:

- la scheda destra e il punto di edit
- la colonna centrale resta solo read-only
- l'apertura della scheda puo avvenire tramite CTA `Override` dal blocco `Parametri di calcolo`
- la scheda deve riusare i contract gia esistenti della surface `articoli`, senza inventare un dominio parallelo

## Right Column Contract - Second Slice

### Scheda `Proposal`

Scopo:

- rappresentare la proposta contestuale del candidate selezionato
- rendere leggibile la logica proposal effettiva
- mostrare la quantita proposta e lo stato di esportabilita
- permettere l'inclusione nel batch export

Vincolo V1:

- nessun override nel primo slice della proposal column

Regola di apertura:

- la scheda `Proposal` deve essere visibile direttamente quando un candidate e selezionato nella colonna sinistra
- il cambio selezione deve aggiornare immediatamente la proposta contestuale resa nella colonna destra

### Ordine dei blocchi

La scheda `Proposal` deve seguire questo ordine:

1. `Header proposta`
2. `Quantita proposta`
3. `Descrizione / Immagine`
4. `Materiale + mm necessari`
5. `Logica proposal`
6. `Warnings / Diagnostica locale`
7. `Azioni`

### 1. Header proposta

Sempre visibile.

Campi:

- `article_code`
- `measure`
- `proposal_status`

Regole:

- l'header deve restare molto compatto
- `proposal_status` va reso come badge forte

### 2. Quantita proposta

Sempre visibile.

Campi:

- `proposal_qty_computed`
- `note_fragment`

Regole:

- il blocco deve privilegiare la lettura operativa:
  - `quantita + note`
- esempio target:
  - `3 pz`
  - `100 pz — BAR x4`
- `measure` non deve essere il secondo dato dominante del blocco
- nessun override quantita in questo slice

### 3. Descrizione / Immagine

Sempre visibile.

Campi:

- `display_description`
- `codice_immagine`
- eventuale preview immagine
  - solo se supportata realmente dall'applicazione

Regole:

- la descrizione deve essere visibile prima del blocco logica
- se la preview immagine non e disponibile, il blocco puo mostrare solo `codice_immagine`

### 4. Materiale + mm necessari

Visibile quando rilevante per la logica effettiva.

Campi:

- `raw_material_article_code`
- `raw_bar_length_mm`
- `usable_mm_per_piece`

Regole:

- il blocco deve spiegare il contesto materiale e i mm necessari
- non deve duplicare inutilmente il dettaglio export completo

### 5. Logica proposal

Sempre visibile.

Campi:

- `requested_proposal_logic_key`
- `effective_proposal_logic_key`
- `proposal_fallback_reason`
- `proposal_logic_article_params`
  - solo parametri rilevanti e valorizzati
- label/description human-friendly della logica effettiva

Regole:

- se non esiste fallback, `proposal_fallback_reason` puo essere nascosto
- i params non devono essere mostrati come JSON grezzo se esiste una resa leggibile

### 6. Warnings / Diagnostica locale

Sempre visibile.

Campi:

- `proposal_status`
- `proposal_fallback_reason`
- `proposal_local_warnings`
- `proposal_reason_summary`

Vocabolario minimo atteso:

- `Error`
- `Need review`
- `Valid for export`

Regole:

- qui vivono solo segnali locali proposal
- non warning planning canonici
- il blocco sostituisce la vecchia card separata `Stato export`

### 7. Azioni

Sempre visibile.

Azioni minime:

- `Aggiungi al batch export`
- `Rimuovi dal batch`

### Campi esclusi in V1

- `proposal_qty_override`
- `proposal_qty_final`
- cambio manuale logica
- note manuali
- editing params proposal
- export diretto dal pannello
- batch editor multi-riga

## Toolbar

La toolbar V1 deve restare minima.

### Ricerca

Ricerca per:

- `article_code`
- `article_description`
- `requested_destination_display`

Regole:

- la ricerca `article_code` deve riusare la normalizzazione gia adottata in `articoli`
- equivalenza UX minima:
  - `.` -> `x`
- la ricerca `article_description` resta testuale
- la ricerca cliente opera su:
  - `requested_destination_display`

### Filtro famiglia

Filtro opzionale per `family_name` / `famiglia articolo`.

Serve per:

- restringere il focus operativo
- supportare verifica e debug

### Filtro scope

La vista deve esporre:

- `Tutti`
- `Solo clienti`
- `Solo magazzino`

Semantica:

- `Solo clienti`
  - include:
    - `Cliente`
    - `Cliente + Magazzino`
- `Solo magazzino`
  - include solo casi `stock-only`

### Filtro `Orizzonte cliente`

La vista deve esporre un filtro denominato:

- `Orizzonte cliente`

Default:

- `365 giorni`

Regole:

- il naming deve essere esplicito e non ambiguo
- non usare la forma generica `entro X giorni`
- il filtro agisce solo sulla componente cliente del calcolo
- la componente scorta continua a usare il proprio orizzonte:
  - `mesi scorta`

Conseguenze UI:

- un candidate misto puo restare misto, diventare `Magazzino` o sparire
- il filtro non deve suggerire che tutta la vista sia filtrata da una data unica

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

Questa spec non chiude ancora:

- dettaglio della colonna destra
- regole complete di batch multi-riga
- score o ranking composito reale
- raggruppamenti avanzati
- drill-down per riga ordine
- editing di policy dalla stessa vista

## Notes

- La surface resta intenzionalmente piu vicina a `criticita` che a un planner completo.
- Lo stato attuale include gia il branching reale `by_article` / `by_customer_order_line`.
- Le future evoluzioni potranno introdurre:
  - contratto completo della colonna centrale
  - contratto completo della colonna destra
  - policy di aggregazione piu ricche
  - slice temporali
  - scoring reale

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
