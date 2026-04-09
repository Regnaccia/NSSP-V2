# ODE V2 - UI Surfaces Overview

## Scopo

Questo documento riassume le schermate UI oggi presenti nella V2, con focus su:

- funzione operativa della schermata
- entita logiche e fact del `core` da cui dipende
- dati esposti
- azioni utente principali

Non sostituisce:

- i `DL-UIX`
- le `UIX_SPEC_*`
- i singoli task

Serve come mappa rapida per capire "cosa fa la schermata" senza dover inseguire subito task e codice.

## Regole generali

- la UI legge da API/Core, mai direttamente dai mirror `sync_*`
- i dati Easy sono mostrati come read-only
- i dati interni V2 sono configurabili solo dove esiste una logica esplicita
- i refresh sono backend-controlled

## 1. Admin

### Funzione

Gestione accessi e identita applicative.

### Dipendenze documentali

DL:

- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/ARCH/DL-ARCH-V2-006.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`

Task:

- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
- `docs/task/TASK-V2-005-admin-access-management.md`
- `docs/task/TASK-V2-006-ui-navigation-refactor.md`
- `docs/task/TASK-V2-017-sidebar-navigation-contestuale.md`

### Entita logiche usate

- `users`
- `roles`
- `user_roles`
- `available_surfaces`

### Cosa espone

- elenco utenti
- stato attivo/inattivo
- ruoli assegnati
- surface disponibili in base ai ruoli

### Azioni principali

- creare/modificare utenti
- attivare/disattivare utenti
- assegnare o rimuovere ruoli

### Note

- e la prima surface amministrativa della V2
- non dipende da Easy

## 2. Logistica - Clienti / Destinazioni

### Funzione

Consultazione e configurazione minima del dominio clienti/destinazioni.

### Dipendenze documentali

DL:

- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`

Task:

- `docs/task/TASK-V2-010-sync-clienti-reale.md`
- `docs/task/TASK-V2-011-sync-destinazioni.md`
- `docs/task/TASK-V2-012-core-clienti-destinazioni.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`
- `docs/task/TASK-V2-014-sync-on-demand-clienti-destinazioni.md`
- `docs/task/TASK-V2-015-destinazione-principale-derivata.md`
- `docs/task/TASK-V2-016-ui-scroll-colonne-clienti-destinazioni.md`

### Pattern UI

- layout a `3 colonne`

### Entita logiche usate

- `clienti`
- `destinazioni`
- destinazione principale derivata dal cliente
- `nickname_destinazione`

### Cosa espone

Colonna 1:

- elenco clienti

Colonna 2:

- destinazione principale
- destinazioni aggiuntive

Colonna 3:

- dati anagrafici read-only
- `nickname_destinazione`

### Azioni principali

- selezione cliente
- selezione destinazione
- modifica `nickname_destinazione`
- refresh on demand logistica

### Dipendenze Core

- Core `clienti + destinazioni`
- regola architetturale della destinazione principale derivata

## 3. Produzione - Articoli

### Funzione

Consultazione anagrafica articoli e configurazione minima di dominio.

### Dipendenze documentali

DL:

- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`

Task:

- `docs/task/TASK-V2-018-sync-articoli-reale.md`
- `docs/task/TASK-V2-019-core-articoli.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-021-sync-on-demand-articoli.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-023-ui-famiglia-articoli.md`
- `docs/task/TASK-V2-024-filtro-famiglia-articoli.md`
- `docs/task/TASK-V2-025-ui-tabella-famiglia-articoli.md`
- `docs/task/TASK-V2-026-gestione-famiglie-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`
- `docs/task/TASK-V2-038-giacenza-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-045-set-aside-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-051-refresh-sequenziale-articoli-con-availability.md`
- `docs/task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md`
- `docs/task/TASK-V2-053-refresh-sequenziale-articoli-con-commitments.md`
- `docs/task/TASK-V2-054-refresh-semantici-backend.md`

### Pattern UI

- layout a `2 colonne`

### Entita logiche usate

- `articoli`
- `famiglie articolo`
- `inventory_positions`
- `customer_set_aside`
- `commitments`
- `availability`

### Cosa espone

Colonna 1:

- lista articoli
- ricerca articolo
- filtro famiglia

Colonna 2:

- dati anagrafici read-only Easy
- `famiglia articolo`
- `giacenza`
- `customer_set_aside`
- `committed_qty`
- `availability_qty`

### Azioni principali

- selezione articolo
- modifica `famiglia articolo`
- gestione catalogo famiglie
- refresh on demand articoli

### Catena dati principale

La schermata articoli si appoggia a:

- `sync_articoli`
- `sync_mag_reale`
- `sync_righe_ordine_cliente`
- `sync_produzioni_attive`
- Core `articoli`
- Core `inventory_positions`
- Core `customer_set_aside`
- Core `commitments`
- Core `availability`

### Note

- e oggi la schermata piu trasversale tra anagrafica, stock e domanda
- viene usata anche come punto di validazione visiva dei fact canonici
- il refresh e oggi un refresh semantico backend (`refresh_articoli`) con chain interna completa

## 4. Produzione - Catalogo Famiglie Articolo

### Funzione

Gestione del catalogo interno `famiglie articolo`.

### Dipendenze documentali

DL:

- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`

Task:

- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-025-ui-tabella-famiglia-articoli.md`
- `docs/task/TASK-V2-026-gestione-famiglie-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`

### Entita logiche usate

- `famiglia articolo`

### Cosa espone

- elenco famiglie
- stato attivo/inattivo
- flag `considera_in_produzione`

### Azioni principali

- creare famiglia
- attivare/disattivare famiglia
- modificare `considera_in_produzione`

### Note

- e una schermata di supporto al dominio articoli
- non dipende da Easy

## 5. Produzioni

### Funzione

Consultazione operativa delle produzioni attive/storiche e del loro stato applicativo.

### Dipendenze documentali

DL:

- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`

Task:

- `docs/task/TASK-V2-028-sync-produzioni-attive.md`
- `docs/task/TASK-V2-029-sync-produzioni-storiche.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`
- `docs/task/TASK-V2-032-sync-on-demand-produzioni.md`
- `docs/task/TASK-V2-033-forza-completata-produzioni.md`
- `docs/task/TASK-V2-034-performance-produzioni-active-default.md`
- `docs/task/TASK-V2-035-filtri-e-ricerca-produzioni.md`

### Pattern UI

- layout a `2 colonne`

### Entita logiche usate

- `produzioni`
- `bucket`
- `stato_produzione`
- `forza_completata`

### Cosa espone

Colonna 1:

- lista produzioni
- bucket `active | historical`
- ricerca per articolo/documento
- filtro stato produzione

Colonna 2:

- dettaglio read-only della produzione
- bucket
- stato produzione
- evidenza del flag `forza_completata`

### Azioni principali

- selezione produzione
- refresh on demand produzioni
- impostazione/rimozione `forza_completata`

### Catena dati principale

- `sync_produzioni_attive`
- `sync_produzioni_storiche`
- Core `produzioni`

## 6. Relazione tra schermate e fact canonici

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

## 7. Prossimi step UI naturali

- decidere in futuro se introdurre una schermata dedicata a:
  - stock / disponibilita
  - ordini cliente
  - commitments

## References

- `docs/SYSTEM_OVERVIEW.md`
- `docs/roadmap/STATUS.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
