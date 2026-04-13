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
