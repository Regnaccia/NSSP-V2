# ODE V2 - UI Surfaces Overview

## Scopo

Questo documento riassume le schermate UI oggi presenti nella V2, con focus su:

- funzione operativa della schermata
- entita logiche e fact del `core` da cui dipende
- dati esposti
- azioni utente principali

## Regole generali

- la UI legge da API/Core, mai direttamente dai mirror `sync_*`
- i dati Easy sono mostrati come read-only
- i refresh sono backend-controlled
- un pulsante `Aggiorna` non deve limitarsi a un reload locale se la vista dipende da fact derivati a monte

## 1. Admin

### Funzione

Gestione accessi e configurazioni interne trasversali.

### Entita logiche usate

- `users`
- `roles`
- `user_roles`
- configurazione warning visibility

### Cosa espone

- elenco utenti
- stato attivo/inattivo
- ruoli assegnati
- pagina admin per configurare la visibilita warning

### Azioni principali

- creare/modificare utenti
- attivare/disattivare utenti
- assegnare o rimuovere ruoli
- configurare la visibilita warning

### Note

- la warning visibility usa `visible_to_areas`
- `admin` governa la configurazione e mantiene vista trasversale

## 2. Logistica - Clienti / Destinazioni

### Funzione

Consultazione e configurazione minima del dominio clienti/destinazioni.

### Entita logiche usate

- `clienti`
- `destinazioni`
- destinazione principale derivata
- `nickname_destinazione`

### Cosa espone

- elenco clienti
- destinazioni del cliente
- dettaglio anagrafico read-only
- `nickname_destinazione`

### Azioni principali

- selezione cliente
- selezione destinazione
- modifica `nickname_destinazione`
- refresh on demand logistica

## 3. Produzione - Articoli

### Funzione

Consultazione anagrafica articoli, configurazione minima di dominio e validazione dei fact quantitativi.

### Entita logiche usate

- `articoli`
- `famiglie articolo`
- `inventory_positions`
- `customer_set_aside`
- `commitments`
- `availability`
- planning policy override articolo
- planning policy effettive articolo

### Cosa espone

- lista articoli
- ricerca `codice`
- ricerca `descrizione`
- filtro famiglia
- dati anagrafici Easy read-only
- `famiglia articolo`
- override tri-state:
  - `considera_in_produzione`
  - `aggrega_codice_in_produzione`
- valori effettivi:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
  - `planning_mode`
- metriche quantitative:
  - `giacenza`
  - `customer_set_aside`
  - `committed_qty`
  - `availability_qty`

### Azioni principali

- selezione articolo
- modifica `famiglia articolo`
- modifica override planning policy
- refresh on demand articoli

### Note

- e la schermata piu trasversale tra anagrafica, stock e domanda
- usa `refresh_articoli()` come refresh semantico completo

## 4. Produzione - Catalogo Famiglie Articolo

### Funzione

Gestione del catalogo interno `famiglie articolo` e dei default di planning policy.

### Entita logiche usate

- `famiglia articolo`

### Cosa espone

- elenco famiglie
- stato attivo/inattivo
- default planning policy:
  - `considera_in_produzione`
  - `aggrega_codice_in_produzione`
- vocabolario planning allineato a:
  - `by_article`
  - `by_customer_order_line`

### Azioni principali

- creare famiglia
- attivare/disattivare famiglia
- modificare i default di planning policy

## 5. Produzioni

### Funzione

Consultazione operativa delle produzioni attive/storiche e del loro stato applicativo.

### Entita logiche usate

- `produzioni`
- `bucket`
- `stato_produzione`
- `forza_completata`

### Cosa espone

- lista produzioni
- bucket `active | historical`
- ricerca per articolo/documento
- filtro stato produzione
- dettaglio read-only della produzione
- evidenza del flag `forza_completata`

### Azioni principali

- selezione produzione
- refresh on demand produzioni
- impostazione/rimozione `forza_completata`

## 6. Produzione - Planning Candidates

### Funzione

Vista operativa planning customer-driven, capace di mostrare sia candidate aggregati per articolo sia candidate per riga ordine cliente.

### Entita logiche usate

- `planning_candidates`
- `availability`
- `produzioni`
- `articoli`
- `famiglie articolo`
- planning policy effettive articolo
- `planning_mode`

### Cosa espone

- codice articolo
- descrizione
- famiglia
- `planning_mode`
- `reason`
- per il ramo `by_article`:
  - `customer_open_demand_qty`
  - `availability_qty`
  - `incoming_supply_qty`
  - `future_availability_qty`
- per il ramo `by_customer_order_line`:
  - `order_reference`
  - `line_reference`
  - `misura`
  - descrizione ordine primaria
  - `line_open_demand_qty`
  - `linked_incoming_supply_qty`
  - `line_future_coverage_qty`
- `required_qty_minimum`

### Azioni principali

- refresh on demand planning, che riusa `refresh_articoli()`
- filtro per famiglia
- ricerca per `codice` e `descrizione`
- toggle del perimetro `effective_considera_in_produzione`
- ordinamento tabellare

### Note

- `incoming_supply_qty` esclude le produzioni completate, anche via override
- la logica planning usa stock clampato a zero

## 7. Produzione - Warnings

### Funzione

Consultazione esplicita del modulo trasversale `Warnings`.

### Entita logiche usate

- `warnings`
- configurazione admin della warning visibility

### Cosa espone

- tipo warning
- severita
- entita / articolo
- messaggio
- giacenza calcolata
- quantita anomala
- timestamp di rilevazione

### Azioni principali

- consultazione lista warning

### Note

- oggi il primo tipo warning e `NEGATIVE_STOCK`
- la surface esiste gia ed e dedicata
- gli utenti operativi vedono solo warning coerenti con la propria area
- `admin` vede la lista trasversale completa

## 8. Produzione - Criticita Articoli

### Funzione

Vista legacy degli articoli critici, basata su `availability_qty < 0`.

### Entita logiche usate

- `availability`
- `commitments`
- `customer_set_aside`
- `inventory_positions`
- `articoli`
- `famiglie articolo`

### Cosa espone

- lista articoli critici
- descrizione articolo
- famiglia
- `giacenza`
- `appartata`
- `impegnata`
- `disponibilita`

### Azioni principali

- refresh on demand criticita, che riusa `refresh_articoli()`
- attivazione/disattivazione del perimetro `considera_in_produzione`
- filtro per famiglia
- ordinamento per famiglia e campi quantitativi

### Note

- resta disponibile ma non e piu la surface primaria
- la deprecazione formale e aperta in `TASK-V2-080`

## 9. Relazione tra schermate e fact canonici

### Inventory

Usato oggi in:

- dettaglio `articoli`

### Customer Set Aside

Usato oggi in:

- dettaglio `articoli`

### Commitments

Usato oggi in:

- dettaglio `articoli`

### Availability

Usato oggi in:

- dettaglio `articoli`
- vista `Planning Candidates`
- vista `criticita articoli`

### Planning Candidates

Usato oggi in:

- vista `Planning Candidates`

### Warnings

Usato oggi in:

- vista `Warnings`

## 10. Prossimi step UI naturali

- integrare badge warning in:
  - `articoli`
  - `Planning Candidates`
- deprecare formalmente `criticita articoli` senza rimozione tecnica

## References

- `docs/SYSTEM_OVERVIEW.md`
- `docs/roadmap/STATUS.md`
