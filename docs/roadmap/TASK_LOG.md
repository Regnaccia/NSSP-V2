# ODE V2 - Task Log

## Scopo

Questo file tiene traccia in forma minimale dei task svolti nella V2.

Regola:

- una riga per task
- descrizione molto breve
- orientato allo storico, non alla pianificazione

Per dettagli tecnici, verifiche e completion contract restano autoritativi i singoli file in `docs/task/`.

## Log

| Task | Stato | Sintesi minima |
|------|-------|----------------|
| `TASK-V2-001` | Completed | Bootstrap backend minimo V2 |
| `TASK-V2-002` | Completed | Hardening verifica backend e completion contract |
| `TASK-V2-003` | Completed | Bootstrap DB interno, migration iniziale e seed minimo |
| `TASK-V2-004` | Completed | Auth browser con ruoli e routing iniziale |
| `TASK-V2-005` | Completed | Surface `admin` per gestione utenti e ruoli |
| `TASK-V2-006` | Completed | Refactor navigazione multi-surface |
| `TASK-V2-007` | Completed | Bootstrap storico sync `clienti` con sorgente fake |
| `TASK-V2-008` | Completed | Hardening verifica backend e scaffolding sync condiviso |
| `TASK-V2-009` | Completed | Schema explorer Easy e catalogo JSON |
| `TASK-V2-010` | Completed | Sync reale `clienti` da `ANACLI` |
| `TASK-V2-011` | Completed | Sync reale `destinazioni` da `POT_DESTDIV` |
| `TASK-V2-012` | Completed | Core `clienti + destinazioni` |
| `TASK-V2-013` | Completed | UI clienti/destinazioni a 3 colonne |
| `TASK-V2-014` | Completed | Sync on demand logistica backend-controlled |
| `TASK-V2-015` | Completed | Destinazione principale derivata dal cliente |
| `TASK-V2-016` | Completed | Scroll indipendente colonne clienti/destinazioni |
| `TASK-V2-017` | Completed | Sidebar navigation contestuale |
| `TASK-V2-018` | Completed | Sync reale `articoli` da `ANAART` |
| `TASK-V2-019` | Completed | Core `articoli` minimale |
| `TASK-V2-020` | Completed | UI `articoli` a 2 colonne |
| `TASK-V2-021` | Completed | Sync on demand `articoli` backend-controlled |
| `TASK-V2-022` | Completed | Catalogo famiglie e associazione articolo -> famiglia |
| `TASK-V2-023` | Completed | Campo configurabile `famiglia` nella UI articoli |
| `TASK-V2-024` | Completed | Filtro famiglia articoli con `Tutti`, `Non configurati` e famiglie specifiche |
| `TASK-V2-025` | Completed | UI dedicata alla tabella `famiglie articolo` |
| `TASK-V2-026` | Completed | Inserimento nuove famiglie e toggle attivo/disattivo |
| `TASK-V2-027` | Completed | Flag booleano `considera_in_produzione` nel catalogo famiglie |
| `TASK-V2-028` | Completed | Sync produzioni attive da `DPRE_PROD` |
| `TASK-V2-029` | Completed | Sync produzioni storiche da `SDPRE_PROD` |
| `TASK-V2-030` | Completed | Core `produzioni` con bucket, stato computato e override |
| `TASK-V2-031` | Completed | UI `produzioni` consultiva a 2 colonne |
| `TASK-V2-032` | Completed | Sync on demand `produzioni` backend-controlled |
| `TASK-V2-033` | Completed | Gestione operativa del flag `forza_completata` |
| `TASK-V2-034` | Completed | Performance `produzioni` con default `active` e storico esplicito |
| `TASK-V2-035` | Completed | Filtro `stato_produzione` e ricerca per articolo/documento |
| `TASK-V2-036` | Completed | Sync `MAG_REALE` come mirror append-only incrementale |
| `TASK-V2-037` | Completed | Computed fact canonica `inventory_positions` da movimenti magazzino |
| `TASK-V2-038` | Completed | Esposizione della giacenza nel dettaglio UI `articoli` |
| `TASK-V2-039` | Completed | Refresh sequenziale `articoli -> mag_reale -> inventory_positions` per la surface articoli |
| `TASK-V2-040` | Completed | Mirror sync read-only di `V_TORDCLI` come base delle righe ordine cliente |
| `TASK-V2-041` | Completed | Core `customer_order_lines` con `open_qty` e `description_lines` |
| `TASK-V2-042` | Completed | Computed fact `commitments` da `customer_order_lines` |
| `TASK-V2-043` | Completed | Estensione `commitments` alla provenienza `production` per materiali `CAT_ART1 != 0` |
| `TASK-V2-044` | Completed | Computed fact `customer_set_aside` da `DOC_QTAP` |
| `TASK-V2-045` | Completed | Esposizione read-only del `customer_set_aside` nel dettaglio UI `articoli` |
| `TASK-V2-046` | Completed | Estensione del refresh articoli per ricalcolare anche `customer_set_aside` |
| `TASK-V2-047` | Completed | Refresh articoli esteso con `sync_righe_ordine_cliente` prima di `customer_set_aside` |
| `TASK-V2-048` | Completed | Correzione della sync ordini cliente per rimuovere dal mirror le righe non piu in `V_TORDCLI` |
| `TASK-V2-049` | Completed | Computed fact `availability` da `inventory`, `customer_set_aside` e `commitments` |
| `TASK-V2-050` | Completed | Esposizione read-only di `committed_qty` e `availability_qty` nel dettaglio UI `articoli` |
| `TASK-V2-051` | Completed | Estensione del refresh articoli per ricalcolare anche `availability` |
| `TASK-V2-052` | Completed | Hardening dei confronti `article_code` cross-source con helper condivisa `normalize_article_code` |
| `TASK-V2-053` | Completed | Estensione del refresh articoli per aggiornare `commitments` cliente e produzione prima di `availability` |
| `TASK-V2-054` | Completed | Refactor backend verso refresh semantici con dipendenze interne e skip downstream su prerequisiti falliti |
| `TASK-V2-055` | Completed | Prima vista operativa minima di criticita articoli basata su `availability_qty < 0` |
| `TASK-V2-056` | Completed | Refinement UI criticita articoli con perimetro `considera_in_produzione`, filtro famiglia e ordinamenti quantitativi |
| `TASK-V2-057` | Completed | Toggle del filtro `considera_in_produzione` nella vista criticita, con default attivo e disattivazione per debug |
| `TASK-V2-058` | Completed | Pulsante `Aggiorna` della vista criticita collegato al refresh semantico completo della surface articoli |
| `TASK-V2-059` | Completed | Hardening delle join cross-source della vista criticita sulla chiave articolo canonica |
| `TASK-V2-060` | Completed | Perimetro criticita ristretto ai soli articoli presenti e attivi nella surface articoli |
| `TASK-V2-061` | Completed | Separazione della ricerca articoli in campi distinti `codice` e `descrizione` |
| `TASK-V2-062` | Completed | Primo slice Core di Planning Candidates V1 customer-driven aggregato per articolo |
| `TASK-V2-063` | Completed | Evoluzione del modello `famiglia + articolo` per planning policy di default e override |
| `TASK-V2-064` | Completed | Esposizione nel Core `articoli` dei valori effettivi delle planning policy |
| `TASK-V2-065` | Completed | Prima surface UI di Planning Candidates V1 aggregata per articolo |
| `TASK-V2-066` | Completed | Estensione della UI famiglie ai default di planning policy |
| `TASK-V2-067` | Completed | Introduzione nel dettaglio articoli di override ed effective planning policy |
| `TASK-V2-068` | Completed | Hardening di Planning Candidates per escludere le produzioni completate, anche via override |
| `TASK-V2-069` | Completed | Allineamento della nomenclatura planning al vocabolario esplicito `planning_mode` |
| `TASK-V2-070` | Completed | Allineamento della UI planning al vocabolario esplicito `planning_mode` |
| `TASK-V2-071` | Completed | Evoluzione del Core Planning Candidates al branching reale `by_article` / `by_customer_order_line` |
| `TASK-V2-072` | Completed | Evoluzione della UI Planning Candidates per rappresentare il branching reale `by_article` / `by_customer_order_line` |
| `TASK-V2-073` | Completed | Re-bootstrap completo di `sync_mag_reale`, riallineamento exact-match con Easy e rebuild della chain inventory -> availability |
| `TASK-V2-074` | Completed | Refinement finale del Core Planning Candidates: clamp stock a zero, reason esplicita, descrizione ordine e misura |
| `TASK-V2-075` | Completed | Refinement finale della UI Planning Candidates: reason, misura e descrizione ordine nel ramo per-riga |
| `TASK-V2-076` | Completed | Primo slice Core del modulo trasversale Warnings con tipo iniziale `NEGATIVE_STOCK` |
| `TASK-V2-077` | Completed | Prima configurazione admin della visibilita warning, ancora modellata per surface |
| `TASK-V2-078` | Completed | Prima surface UI dedicata del modulo `Warnings`, con filtro implicito sulla visibilita configurata |
| `TASK-V2-079` | Deferred | Integrazione badge warning in `articoli` e `Planning Candidates`, parcheggiata per lasciare `Warnings` come modulo autonomo |
| `TASK-V2-080` | Completed | Deprecazione formale della surface `criticita articoli` senza rimozione tecnica |
| `TASK-V2-081` | Completed | Riallineamento warning visibility da surface a aree/reparti operativi |
| `TASK-V2-082` | Completed | Correzione della surface `Warnings` per filtrare i warning per area/reparto corrente con bypass admin |
| `TASK-V2-083` | Completed | Modello configurativo stock policy V1 con default famiglia e override articolo |
| `TASK-V2-084` | Completed | Core stock policy metrics V1 con strategy attiva configurata per `monthly_stock_base_qty` e capacity setup fissa |
| `TASK-V2-085` | Completed | Integrazione stock-driven nel ramo `Planning Candidates by_article` con candidate unico e breakdown cliente/scorta |
| `TASK-V2-086` | Completed | Configurazione interna delle logiche stock con `strategy_key`, `params_json` e capacity setup non switchabile |
| `TASK-V2-087` | Completed | Hardening dell'algoritmo `monthly_stock_base_from_sales_v1` con finestre multiple, percentile e outlier filtering |
| `TASK-V2-088` | Completed | Allineamento finale stock policy V1: fallback `None`, `min_movements`, `rounding_scale`, perimetro `by_article` e driver movimenti esplicito |
| `TASK-V2-089` | Completed | Esposizione nella surface `articoli` di metriche stock, capacity e configurazioni effettive della stock policy |
| `TASK-V2-090` | Completed | Configurazione admin delle logiche stock V1: strategy, parametri e capacity logic fissa |
| `TASK-V2-091` | Completed | Nuovo warning `INVALID_STOCK_CAPACITY` per articoli stock-driven con `capacity` invalida o assente |
| `TASK-V2-092` | Completed | Riallineamento di `capacity_from_containers_v1` alla formula legacy con contenitori, peso articolo e fallback corretti |
| `TASK-V2-093` | Completed | Estensione UI `famiglie articolo` ai default quantitativi `stock_months` e `stock_trigger_months` |
| `TASK-V2-094` | Completed | Refinement admin stock logic con sezione dedicata e configurazione dei `capacity_logic_params` |
| `TASK-V2-095` | Completed | Separazione della governance stock in una pagina admin dedicata distinta dalla pagina utenti |
| `TASK-V2-096` | Completed | Introduzione del flag esplicito `gestione_scorte_attiva` con default famiglia, override articolo e valore effettivo |
| `TASK-V2-097` | Completed | Estensione UI `famiglie articolo` al default `gestione_scorte_attiva` |
| `TASK-V2-098` | Completed | Estensione UI `articoli` all'override `gestione_scorte_attiva` e al valore effettivo |
| `TASK-V2-099` | Completed | Riallineamento Core stock policy e Planning Candidates al prerequisito `effective_gestione_scorte_attiva` |
| `TASK-V2-100` | Completed | Primo `customer horizon` Core per i candidate cliente, basato su `data_consegna` e senza scartare i fuori orizzonte |
| `TASK-V2-101` | Completed | Introduzione di `stock horizon` nel ramo `by_article` con cap temporale sugli impegni per la sola componente scorta |
| `TASK-V2-102` | Completed | Filtri UI `Planning Candidates` per `Tutti / Solo fabbisogno cliente / Solo scorta` e filtro `customer horizon` |
| `TASK-V2-103` | Completed | Separazione Core tra `customer horizon` e `stock horizon`, eliminando l'accoppiamento improprio |
| `TASK-V2-104` | Completed | Riallineamento UI/API del filtro `customer horizon` senza side effects sulla componente scorta |
| `TASK-V2-105` | Completed | Classificazione primaria `customer|stock` per evitare doppia presenza dei casi misti |
| `TASK-V2-106` | Completed | Valorizzazione di `required_qty_minimum` nei candidate `stock-only` secondo il driver primario |
| `TASK-V2-107` | Completed | Esposizione della data richiesta in `Planning Candidates` con semantica distinta per ramo aggregato e per-riga |
| `TASK-V2-108` | Completed | Estensione del contratto Core planning per descrizione completa, destinazione richiesta e campi di leggibilita |
| `TASK-V2-109` | Completed | Refinement finale UI `Planning Candidates` con misura, badge famiglia, motivi sintetici e destinazione leggibile |
| `TASK-V2-110` | Completed | Unificazione del modello descrittivo planning con `description_parts` e `display_description` |
| `TASK-V2-111` | Completed | Enrichment Core/API dei warning articolo in `Planning Candidates` |
| `TASK-V2-112` | Completed | Colonna `Warnings` nella tabella `Planning Candidates` con badge sintetici |
| `TASK-V2-113` | Completed | Quick config modal articolo dalla vista `Planning Candidates` |
| `TASK-V2-114` | Completed | Bridge case-insensitive planning -> articoli per lookup e write config articolo |
