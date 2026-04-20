# ODE Documentation

## Struttura

```text
docs/
|-- archive/          documenti V2 non attivi o superseded
|-- charter/          scopo, principi e criteri guida della V2
|-- decisions/        decision log V2 organizzati per tipo
|-- guides/           guide operative e convenzioni V2
|-- integrations/     specifiche tecniche delle integrazioni esterne
|-- roadmap/          sviluppi confermati e punti aperti della V2
|-- task/             task di implementazione passati a Claude Code
`-- test/             report di verifica su task, pipeline e controlli manuali
```

## Overview

| File | Contenuto |
|------|-----------|
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | Panoramica rapida dello stato reale del sistema V2: stream operativi, mirror sync attivi, dati interni, surface e pattern consolidati |
| [AI_HANDOFF_CURRENT_STATE.md](AI_HANDOFF_CURRENT_STATE.md) | Handoff sintetico per un altro agente AI: cosa fa oggi il software, quali fact e surface sono reali, quali limiti restano e da dove iniziare i ragionamenti successivi |

## Specs

| File | Contenuto |
|------|-----------|
| [specs/PLANNING_CANDIDATES_SPEC_V1_1.md](specs/PLANNING_CANDIDATES_SPEC_V1_1.md) | Spec ampia del modulo `Planning Candidates`, utile come intent document e base di ragionamento |
| [specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md](specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md) | Versione ridotta e implementabile della V1 di `Planning Candidates`, allineata al modello canonico attuale della V2 |
| [specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md](specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md) | Estensione ridotta della logica `Planning Candidates` con due modalita esplicite: `by_article` e `by_customer_order_line` |
| [specs/STOCK_POLICY_V1_REDUCED_SPEC.md](specs/STOCK_POLICY_V1_REDUCED_SPEC.md) | Versione ridotta e implementabile della prima stock policy V1, limitata al ramo `by_article`, con `strategy selection` per `monthly_stock_base_qty`, capacity setup fissa e riuso di `future_availability_qty` |
| [specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md](specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md) | Spec del modulo `Production Proposals` riallineata al flusso reale V2: selezione in planning, workspace temporaneo, persistenza solo all'export, export `xlsx` EasyJob, fallback proposal a pezzi e logica `full bar` V1 |
| [specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md](specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md) | Versione ridotta e implementabile della V1 di `Production Proposals`, centrata su workspace temporanei downstream di `Planning Candidates`, logiche proposal articolo-based, export `xlsx` e reconcile |
| [specs/WARNINGS_SPEC_V1.md](specs/WARNINGS_SPEC_V1.md) | Spec iniziale del modulo trasversale `Warnings`, con warning canonici unici e visibilita differenziata per surface o ruolo |

## Reviews

| File | Contenuto |
|------|-----------|
| [reviews/README.md](reviews/README.md) | Indice delle review critiche trasversali sullo stato del progetto |
| [reviews/KNOWN_BUGS.md](reviews/KNOWN_BUGS.md) | Registro dei bug e limiti noti che richiedono memoria operativa o architetturale oltre il singolo task |
| [reviews/PROJECT_REVIEW_2026-04-08.md](reviews/PROJECT_REVIEW_2026-04-08.md) | Review architetturale e operativa del progetto V2, con finding, rischi potenziali e linea di risoluzione |
| [reviews/PROJECT_REVIEW_2026-04-15_GENERAL.md](reviews/PROJECT_REVIEW_2026-04-15_GENERAL.md) | Review generale aggiornata della V2, con valutazione dei moduli, punti di frammentazione, debiti backbone e proposta di rebase architetturale leggero |

## Charter

| File | Contenuto |
|------|-----------|
| [charter/V2_CHARTER.md](charter/V2_CHARTER.md) | Charter principale della V2 |

## Decisions

Sottocartelle per tipo:

- `ARCH/`
- `OPS/`
- `UIX/`

| File | Contenuto |
|------|-----------|
| [decisions/ARCH/DL-ARCH-V2-001.md](decisions/ARCH/DL-ARCH-V2-001.md) | Struttura repository V2 e confini espliciti tra sync, core e app |
| [decisions/ARCH/DL-ARCH-V2-002.md](decisions/ARCH/DL-ARCH-V2-002.md) | Verifica riproducibile dei task e completion contract |
| [decisions/ARCH/DL-ARCH-V2-003.md](decisions/ARCH/DL-ARCH-V2-003.md) | Database interno V2 come persistence backbone |
| [decisions/ARCH/DL-ARCH-V2-003A.md](decisions/ARCH/DL-ARCH-V2-003A.md) | Modello dati identity/auth adottato nel codice: `users`, `roles`, `user_roles` |
| [decisions/ARCH/DL-ARCH-V2-004.md](decisions/ARCH/DL-ARCH-V2-004.md) | Modello di accesso utente, ruoli e canali client |
| [decisions/ARCH/DL-ARCH-V2-005.md](decisions/ARCH/DL-ARCH-V2-005.md) | Definizione stabile di surfaces applicative e del loro ruolo nel contratto backend/frontend |
| [decisions/ARCH/DL-ARCH-V2-006.md](decisions/ARCH/DL-ARCH-V2-006.md) | Surface `admin` come primo modulo di access management, con lifecycle utenti e regole minime di sicurezza |
| [decisions/ARCH/DL-ARCH-V2-007.md](decisions/ARCH/DL-ARCH-V2-007.md) | Modello di sync per entita, con unita dedicate e separazione esplicita tra Sync e Core |
| [decisions/ARCH/DL-ARCH-V2-008.md](decisions/ARCH/DL-ARCH-V2-008.md) | Modello runtime della sync: job, freshness, bootstrap mode, dipendenze e orchestrazione |
| [decisions/ARCH/DL-ARCH-V2-009.md](decisions/ARCH/DL-ARCH-V2-009.md) | Contratto minimo obbligatorio per ogni sync unit: target interno, source identity, alignment, run metadata e dependency declaration |
| [decisions/ARCH/DL-ARCH-V2-010.md](decisions/ARCH/DL-ARCH-V2-010.md) | Primo slice Core `clienti + destinazioni` come ponte tra target sync interni, dati configurabili di destinazione e surface logistica |
| [decisions/ARCH/DL-ARCH-V2-011.md](decisions/ARCH/DL-ARCH-V2-011.md) | Modello di `sync on demand` governato dal backend, con guard su permessi, dipendenze e concorrenza prima dello scheduler automatico |
| [decisions/ARCH/DL-ARCH-V2-012.md](decisions/ARCH/DL-ARCH-V2-012.md) | Regola Core per trattare il cliente come destinazione principale esplicita, unificata alle destinazioni aggiuntive nel read model operativo |
| [decisions/ARCH/DL-ARCH-V2-013.md](decisions/ARCH/DL-ARCH-V2-013.md) | Primo Core `articoli` minimale come proiezione applicativa dei dati di `sync_articoli`, separato dal mirror e pronto per alimentare la UI |
| [decisions/ARCH/DL-ARCH-V2-014.md](decisions/ARCH/DL-ARCH-V2-014.md) | `Famiglia articolo` come prima entita interna di produzione, con catalogo controllato V2 e associazione agli articoli |
| [decisions/ARCH/DL-ARCH-V2-015.md](decisions/ARCH/DL-ARCH-V2-015.md) | Primo Core `produzioni` aggregato da mirror attivi/storici, con `bucket`, `stato_produzione` computato e override interno `forza_completata` |
| [decisions/ARCH/DL-ARCH-V2-016.md](decisions/ARCH/DL-ARCH-V2-016.md) | `Inventory` / `giacenza articoli` come computed fact canonico del Core, derivato dai movimenti di magazzino e riusabile cross-modulo |
| [decisions/ARCH/DL-ARCH-V2-017.md](decisions/ARCH/DL-ARCH-V2-017.md) | `Impegno` come computed fact canonico del Core, separato da `inventory` e base per la futura `availability` |
| [decisions/ARCH/DL-ARCH-V2-018.md](decisions/ARCH/DL-ARCH-V2-018.md) | `Ordine` come entita canonica cross-modulo, distinta da `commitments` e base per futuri stream cliente, produzione, logistica e disponibilita |
| [decisions/ARCH/DL-ARCH-V2-019.md](decisions/ARCH/DL-ARCH-V2-019.md) | Quantita appartata cliente come fact canonico intermedio, separato da `inventory`, `commitments` e futura `availability` |
| [decisions/ARCH/DL-ARCH-V2-020.md](decisions/ARCH/DL-ARCH-V2-020.md) | `V_TORDCLI` come mirror operativo delle righe ordine cliente attive, con storico delegato a sorgenti Easy separate |
| [decisions/ARCH/DL-ARCH-V2-021.md](decisions/ARCH/DL-ARCH-V2-021.md) | `Availability` come computed fact canonico derivato da `inventory`, `customer_set_aside` e `commitments` |
| [decisions/ARCH/DL-ARCH-V2-022.md](decisions/ARCH/DL-ARCH-V2-022.md) | Refresh backend semantici con dipendenze interne, tracciabilita step-by-step e skip downstream su prerequisiti falliti |
| [decisions/ARCH/DL-ARCH-V2-023.md](decisions/ARCH/DL-ARCH-V2-023.md) | Logiche di dominio come funzioni intercambiabili su fact canonici, separate dai computed fact e sostituibili senza rompere il modello |
| [decisions/ARCH/DL-ARCH-V2-024.md](decisions/ARCH/DL-ARCH-V2-024.md) | Distinzione esplicita tra chiave articolo raw e chiave articolo canonica, con divieto di join diretti misti nei read model e nei fact cross-source |
| [decisions/ARCH/DL-ARCH-V2-025.md](decisions/ARCH/DL-ARCH-V2-025.md) | Prima definizione di `Planning Candidates` come projection customer-driven aggregata per articolo, basata su `future_availability_qty` e supply gia in corso |
| [decisions/ARCH/DL-ARCH-V2-026.md](decisions/ARCH/DL-ARCH-V2-026.md) | Policy operative di planning con default a livello famiglia e override articolo, inclusi `considera_in_produzione` e `aggrega_codice_in_produzione` |
| [decisions/ARCH/DL-ARCH-V2-027.md](decisions/ARCH/DL-ARCH-V2-027.md) | Evoluzione di `Planning Candidates` verso due modalita esplicite di aggregazione: `by_article` e `by_customer_order_line`, governate da `effective_aggrega_codice_in_produzione` |
| [decisions/ARCH/DL-ARCH-V2-028.md](decisions/ARCH/DL-ARCH-V2-028.md) | Refinement finale di `Planning Candidates` prima di `Production Proposals`: stock clampato a zero, reason esplicita, misura esposta e descrizione ordine nel ramo per-riga |
| [decisions/ARCH/DL-ARCH-V2-029.md](decisions/ARCH/DL-ARCH-V2-029.md) | `Warnings` come modulo trasversale canonico: un warning esiste una sola volta e la visibilita per reparti o surface si modella via audience, non con duplicazione |
| [decisions/ARCH/DL-ARCH-V2-030.md](decisions/ARCH/DL-ARCH-V2-030.md) | Prima definizione della stock policy V1 come estensione minima del planning `by_article`, con strategy selection configurabile per `monthly_stock_base_qty` e capacity setup fissa |
| [decisions/ARCH/DL-ARCH-V2-031.md](decisions/ARCH/DL-ARCH-V2-031.md) | Introduzione di `customer horizon`, `stock horizon` e separazione UI tra driver `fabbisogno cliente` e `scorta` senza duplicare il Core planning |
| [decisions/ARCH/DL-ARCH-V2-032.md](decisions/ARCH/DL-ARCH-V2-032.md) | Modello descrittivo unificato di `Planning Candidates`, con `description_parts` e `display_description` comuni ai rami `by_article` e `by_customer_order_line` |
| [decisions/ARCH/DL-ARCH-V2-033.md](decisions/ARCH/DL-ARCH-V2-033.md) | `Production Proposals` V1 rifinito come workspace temporaneo generato da `Planning Candidates`, con persistenza solo all'export e reconcile via `ODE_REF` |
| [decisions/ARCH/DL-ARCH-V2-034.md](decisions/ARCH/DL-ARCH-V2-034.md) | Contratto di export `xlsx` EasyJob per `Production Proposals`, con mapping colonna-per-colonna, validazione bloccante su `ordine` e nota deterministica con `ODE_REF` |
| [decisions/ARCH/DL-ARCH-V2-035.md](decisions/ARCH/DL-ARCH-V2-035.md) | Seconda logica proposal V1 `proposal_full_bar_v1`, con configurazione barra su articolo, flag famiglia per abilitare il campo e fallback obbligatorio a pezzi |
| [decisions/ARCH/DL-ARCH-V2-036.md](decisions/ARCH/DL-ARCH-V2-036.md) | Diagnostica locale di `Production Proposals` per distinguere logica richiesta, logica effettiva e motivo del fallback senza sporcare il modulo `Warnings` |
| [decisions/ARCH/DL-ARCH-V2-037.md](decisions/ARCH/DL-ARCH-V2-037.md) | Correzione di modello: `raw_bar_length_mm` appartiene al materiale grezzo associato e `proposal_full_bar_v1` deve risolverlo via `materiale_grezzo_codice` |
| [decisions/ARCH/DL-ARCH-V2-038.md](decisions/ARCH/DL-ARCH-V2-038.md) | Nuova logica `proposal_full_bar_v2_capacity_floor`: prova `ceil`, poi `floor` sotto capienza, poi fallback a pezzi |
| [decisions/ARCH/DL-ARCH-V2-039.md](decisions/ARCH/DL-ARCH-V2-039.md) | Baseline del rebase architetturale V2: moduli congelati, split `need vs release now`, policy axes proposal, ownership dati e separazione tra domain rebase e backbone hardening |
| [decisions/ARCH/DL-ARCH-V2-040.md](decisions/ARCH/DL-ARCH-V2-040.md) | Primo contratto di rebase di `Planning Candidates`: split `required_qty_eventual / release_qty_now_max / release_status` nel ramo `by_article` |
| [decisions/ARCH/DL-ARCH-V2-041.md](decisions/ARCH/DL-ARCH-V2-041.md) | Target UX post-rebase: `Unified Planning Workspace` come surface operativa primaria, proposal panel contestuale e storico export separato |
| [decisions/ARCH/DL-ARCH-V2-042.md](decisions/ARCH/DL-ARCH-V2-042.md) | Target del rebase planning: Core candidato semplice, `priority_score` come layer separato di urgenza e declassamento di `customer_horizon` a compatibilita transitoria |
| [decisions/ARCH/DL-ARCH-V2-043.md](decisions/ARCH/DL-ARCH-V2-043.md) | Chiusura della scelta di rebase: `customer_horizon` esce dal Core planning e resta solo come filtro UI / segnale di priorita |
| [decisions/ARCH/DL-ARCH-V2-TEMPLATE.md](decisions/ARCH/DL-ARCH-V2-TEMPLATE.md) | Template minimo per nuovi Decision Log architetturali V2 |
| [decisions/UIX/DL-UIX-V2-001.md](decisions/UIX/DL-UIX-V2-001.md) | Modello UI di navigazione multi-surface con layout persistente e sidebar basata su `available_surfaces` |
| [decisions/UIX/DL-UIX-V2-002.md](decisions/UIX/DL-UIX-V2-002.md) | Pattern standard multi-colonna per menu configurazioni, con varianti a `2`, `3` o `4` colonne secondo il nesting del caso |
| [decisions/UIX/DL-UIX-V2-003.md](decisions/UIX/DL-UIX-V2-003.md) | Navigazione contestuale per-surface: livello primario per le surface e livello secondario per le funzioni interne della surface attiva |
| [decisions/UIX/DL-UIX-V2-004.md](decisions/UIX/DL-UIX-V2-004.md) | Normalizzazione standard della ricerca articoli, con equivalenza UX tra separatori dimensionali come `.` e `x` |
| [decisions/UIX/specs/README.md](decisions/UIX/specs/README.md) | Indice delle specifiche UIX dei casi concreti che applicano i pattern generali |
| [decisions/UIX/specs/UIX_SPEC_ARTICOLI.md](decisions/UIX/specs/UIX_SPEC_ARTICOLI.md) | Specifica della variante a `2 colonne` per il caso `articoli`, con lista completa a sinistra e configurazione a destra |
| [decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md](decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md) | Specifica della variante a `3 colonne` per la surface logistica clienti/destinazioni |
| [decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md](decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md) | Specifica della prima surface operativa `Planning Candidates`, aggregata per articolo e coerente con la V1 ridotta del modulo |
| [decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md](decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md) | Specifica della variante a `2 colonne` per la surface `produzioni`, con lista a sinistra e dettaglio read-only a destra |

## Guides

| File | Contenuto |
|------|-----------|
| [guides/BACKEND_BOOTSTRAP_AND_VERIFY.md](guides/BACKEND_BOOTSTRAP_AND_VERIFY.md) | Bootstrap locale backend/frontend, auth browser, admin, logistica, produzione/articoli, sync Easy read-only, catalogo famiglie e sync on demand backend-controlled |
| [guides/COLLABORATION_RULES_REBASE.md](guides/COLLABORATION_RULES_REBASE.md) | Regole operative di collaborazione durante il rebase V2: classificazione delle idee, uso di task/test/DL, gestione dei casi reali e separazione tra bisogno, rilascio e priorita |
| [guides/IMPLEMENTATION_PATTERNS.md](guides/IMPLEMENTATION_PATTERNS.md) | Pattern replicabili emersi dai primi slice reali V2, utili per accelerare nuovi stream di sviluppo |
| [guides/PLANNING_AND_STOCK_RULES.md](guides/PLANNING_AND_STOCK_RULES.md) | Guida breve e normativa per le regole oggi stabili di `Planning Candidates`, stock policy V1, horizon iniziali e warning collegati |
| [guides/UI_SURFACES_OVERVIEW.md](guides/UI_SURFACES_OVERVIEW.md) | Riepilogo delle schermate UI V2 per funzione, entita logiche usate, dati esposti e azioni principali |

## Integrations

| File | Contenuto |
|------|-----------|
| [integrations/README.md](integrations/README.md) | Indice della documentazione tecnica per le integrazioni esterne V2 |
| [integrations/easy/README.md](integrations/easy/README.md) | Documentazione tecnica delle entita Easy lette in read-only |
| [integrations/easy/catalog/README.md](integrations/easy/catalog/README.md) | Catalogo machine-generated degli schemi Easy in formato JSON |
| [integrations/easy/EASY_ARTICOLI.md](integrations/easy/EASY_ARTICOLI.md) | Mapping curato della tabella `ANAART` verso il target interno `sync_articoli` |
| [integrations/easy/EASY_CLIENTI.md](integrations/easy/EASY_CLIENTI.md) | Mapping curato della tabella `ANACLI` verso il target interno `sync_clienti` |
| [integrations/easy/EASY_DESTINAZIONI.md](integrations/easy/EASY_DESTINAZIONI.md) | Mapping curato della tabella `POT_DESTDIV` verso il target interno `sync_destinazioni` |
| [integrations/easy/EASY_MAG_REALE.md](integrations/easy/EASY_MAG_REALE.md) | Mapping curato della tabella `MAG_REALE` come primo caso di mirror `append-only` con sync incrementale previsto |
| [integrations/easy/EASY_PRODUZIONI.md](integrations/easy/EASY_PRODUZIONI.md) | Mapping curato delle sorgenti `DPRE_PROD` e `SDPRE_PROD` verso mirror sync separati per produzioni attive e storiche |
| [integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md](integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md) | Mapping curato della vista `V_TORDCLI` come primo mirror delle righe ordine cliente |
| [integrations/easy/EASY_ENTITY_MAPPING_TEMPLATE.md](integrations/easy/EASY_ENTITY_MAPPING_TEMPLATE.md) | Template per documentare una mappatura Easy verso il target sync interno V2 |

## Roadmap

La cartella `roadmap/` raccoglie stato e roadmap attiva della V2.

| File | Contenuto |
|------|-----------|
| [roadmap/STATUS.md](roadmap/STATUS.md) | Snapshot di stato del progetto: perimetro completato, task aperti e prossima sequenza consigliata |
| [roadmap/TASK_LOG.md](roadmap/TASK_LOG.md) | Log minimale dei task V2 svolti, con una sintesi breve per task |
| [roadmap/REBASE_V2_BACKLOG_2026-04-15.md](roadmap/REBASE_V2_BACKLOG_2026-04-15.md) | Backlog di rebase della V2 dopo la review generale: stream `Domain Rebase`, stream `Backbone Hardening` e rilettura del cluster proposal `115-127` |
| [roadmap/CLEANUP_PLAN_2026-04-17.md](roadmap/CLEANUP_PLAN_2026-04-17.md) | Piano di pulizia prudente della V2: distinzione tra eliminabile subito, archiviabile e compatibilita da tenere finche non verificate |

I documenti oggi considerati piu vicini a V1 sono stati spostati in archivio:

| File | Contenuto |
|------|-----------|
| [archive/ROADMAP/FUTURE.md](archive/ROADMAP/FUTURE.md) | Roadmap storica ereditata dal contesto precedente |
| [archive/ROADMAP/POSSIBLE.md](archive/ROADMAP/POSSIBLE.md) | Ragionamenti aperti ereditati dal contesto precedente |

## Task

| File | Contenuto |
|------|-----------|
| [task/TASK-V2-001-bootstrap-backend.md](task/TASK-V2-001-bootstrap-backend.md) | Bootstrap backend minimo V2 e primo scaffold coerente con i layer architetturali |
| [task/TASK-V2-002-hardening-verifica-backend.md](task/TASK-V2-002-hardening-verifica-backend.md) | Hardening della verifica riproducibile del backend e del completion contract |
| [task/TASK-V2-003-bootstrap-db-interno.md](task/TASK-V2-003-bootstrap-db-interno.md) | Bootstrap del DB interno V2: PostgreSQL locale, modelli strutturali, prima migration e seed minimo |
| [task/TASK-V2-004-browser-auth-and-role-routing.md](task/TASK-V2-004-browser-auth-and-role-routing.md) | Primo slice auth browser con ruoli multipli e routing iniziale coerente |
| [task/TASK-V2-005-admin-access-management.md](task/TASK-V2-005-admin-access-management.md) | Prima surface reale `admin` per gestione utenti, ruoli e stato attivo/inattivo |
| [task/TASK-V2-006-ui-navigation-refactor.md](task/TASK-V2-006-ui-navigation-refactor.md) | Refactor della navigazione browser verso layout persistente multi-surface con sidebar basata su `available_surfaces` |
| [task/TASK-V2-007-bootstrap-sync-clienti.md](task/TASK-V2-007-bootstrap-sync-clienti.md) | Bootstrap tecnico storico della sync `clienti`, basato su sorgente fake e usato per validare il modello sync |
| [task/TASK-V2-008-hardening-backend-verifica-and-sync-scaffolding.md](task/TASK-V2-008-hardening-backend-verifica-and-sync-scaffolding.md) | Hardening della verifica backend e riallineamento dello scaffolding sync condiviso prima del primo caso applicativo reale |
| [task/TASK-V2-009-easy-schema-explorer-and-catalog.md](task/TASK-V2-009-easy-schema-explorer-and-catalog.md) | Script read-only per estrarre lo schema tecnico delle tabelle Easy in JSON e popolare il catalogo documentale |
| [task/TASK-V2-010-sync-clienti-reale.md](task/TASK-V2-010-sync-clienti-reale.md) | Sync reale `clienti` da `ANACLI` verso il target interno V2, usando il mapping documentato e un adapter Easy read-only |
| [task/TASK-V2-011-sync-destinazioni.md](task/TASK-V2-011-sync-destinazioni.md) | Sync reale `destinazioni` da `POT_DESTDIV`, con dipendenza esplicita da `clienti` e target interno dedicato |
| [task/TASK-V2-012-core-clienti-destinazioni.md](task/TASK-V2-012-core-clienti-destinazioni.md) | Primo slice Core `clienti + destinazioni`, con `nickname_destinazione` interno e read model per la futura surface logistica |
| [task/TASK-V2-013-ui-clienti-destinazioni.md](task/TASK-V2-013-ui-clienti-destinazioni.md) | Prima surface browser clienti/destinazioni a 3 colonne, basata sui read model Core e separata dal trigger sync |
| [task/TASK-V2-014-sync-on-demand-clienti-destinazioni.md](task/TASK-V2-014-sync-on-demand-clienti-destinazioni.md) | Trigger `sync on demand` backend-controlled integrato nella surface clienti/destinazioni, senza introdurre ancora scheduler automatico |
| [task/TASK-V2-015-destinazione-principale-derivata.md](task/TASK-V2-015-destinazione-principale-derivata.md) | Integrazione della regola Core per trattare il cliente come destinazione principale esplicita, unificata alle destinazioni aggiuntive nella logica e nella UI |
| [task/TASK-V2-016-ui-scroll-colonne-clienti-destinazioni.md](task/TASK-V2-016-ui-scroll-colonne-clienti-destinazioni.md) | Refinement UI della surface clienti/destinazioni per introdurre colonne scrollabili indipendenti, con focus sulla colonna clienti a sinistra |
| [task/TASK-V2-017-sidebar-navigation-contestuale.md](task/TASK-V2-017-sidebar-navigation-contestuale.md) | Navigazione contestuale nella sidebar: funzioni interne mostrate in base alla surface attiva, mantenendo separati livello surface e livello funzione |
| [task/TASK-V2-018-sync-articoli-reale.md](task/TASK-V2-018-sync-articoli-reale.md) | Sync reale `articoli` da `ANAART` verso il target interno `sync_articoli`, come primo mirror del flusso `produzione` |
| [task/TASK-V2-019-core-articoli.md](task/TASK-V2-019-core-articoli.md) | Primo Core `articoli` come proiezione applicativa dei dati sincronizzati, in attesa di futuri dati interni e della UI a `2 colonne` |
| [task/TASK-V2-020-ui-articoli.md](task/TASK-V2-020-ui-articoli.md) | Prima surface browser `articoli` a `2 colonne`, con lista a sinistra e dettaglio read-only a destra basato sui dati Easy importati |
| [task/TASK-V2-021-sync-on-demand-articoli.md](task/TASK-V2-021-sync-on-demand-articoli.md) | Trigger `sync on demand` backend-controlled per la surface `articoli`, con action UI dedicata e senza introdurre ancora scheduler automatico |
| [task/TASK-V2-022-famiglia-articoli.md](task/TASK-V2-022-famiglia-articoli.md) | Prima entita interna del dominio `articoli`: catalogo famiglie controllato V2 e associazione configurabile articolo -> famiglia |
| [task/TASK-V2-023-ui-famiglia-articoli.md](task/TASK-V2-023-ui-famiglia-articoli.md) | Integrazione nella surface `articoli` del primo campo configurabile interno `famiglia`, mantenendo separati dati Easy read-only e dato interno modificabile |
| [task/TASK-V2-024-filtro-famiglia-articoli.md](task/TASK-V2-024-filtro-famiglia-articoli.md) | Filtro famiglia nella lista articoli, con supporto a `Tutti`, `Non configurati` e famiglie specifiche |
| [task/TASK-V2-025-ui-tabella-famiglia-articoli.md](task/TASK-V2-025-ui-tabella-famiglia-articoli.md) | Vista dedicata alla tabella `famiglie articolo`, separata dalla configurazione del singolo articolo |
| [task/TASK-V2-026-gestione-famiglie-articoli.md](task/TASK-V2-026-gestione-famiglie-articoli.md) | Gestione minima del catalogo famiglie: inserimento nuove famiglie e attivazione/disattivazione |
| [task/TASK-V2-027-flag-considera-in-produzione-famiglie.md](task/TASK-V2-027-flag-considera-in-produzione-famiglie.md) | Aggiunta del flag booleano `considera_in_produzione` nel catalogo famiglie e gestione UI dedicata |
| [task/TASK-V2-028-sync-produzioni-attive.md](task/TASK-V2-028-sync-produzioni-attive.md) | Mirror sync read-only delle produzioni attive da `DPRE_PROD` verso `sync_produzioni_attive` |
| [task/TASK-V2-029-sync-produzioni-storiche.md](task/TASK-V2-029-sync-produzioni-storiche.md) | Mirror sync read-only delle produzioni storiche da `SDPRE_PROD` verso `sync_produzioni_storiche` |
| [task/TASK-V2-030-core-produzioni-bucket-e-stato.md](task/TASK-V2-030-core-produzioni-bucket-e-stato.md) | Primo Core `produzioni` aggregato, con `bucket`, computed fact `stato_produzione` e flag interno `forza_completata` |
| [task/TASK-V2-031-ui-produzioni.md](task/TASK-V2-031-ui-produzioni.md) | Prima surface browser `produzioni` a `2 colonne`, consultiva e basata sul Core aggregato |
| [task/TASK-V2-032-sync-on-demand-produzioni.md](task/TASK-V2-032-sync-on-demand-produzioni.md) | Trigger `sync on demand` backend-controlled per la surface `produzioni`, coerente con il pattern gia usato in logistica e articoli |
| [task/TASK-V2-033-forza-completata-produzioni.md](task/TASK-V2-033-forza-completata-produzioni.md) | Prima gestione operativa del flag interno `forza_completata` nella surface `produzioni` |
| [task/TASK-V2-034-performance-produzioni-active-default.md](task/TASK-V2-034-performance-produzioni-active-default.md) | Hardening prestazionale della surface `produzioni`: default `active`, filtro `bucket` server-side e paginazione backend |
| [task/TASK-V2-035-filtri-e-ricerca-produzioni.md](task/TASK-V2-035-filtri-e-ricerca-produzioni.md) | Refinement della surface `produzioni`: filtro per `stato_produzione` e ricerca per `codice_articolo` / `numero_documento` |
| [task/TASK-V2-036-sync-mag-reale.md](task/TASK-V2-036-sync-mag-reale.md) | Mirror sync read-only dei movimenti `MAG_REALE`, come primo caso `append-only` con sync incrementale |
| [task/TASK-V2-037-core-inventory-positions.md](task/TASK-V2-037-core-inventory-positions.md) | Prima computed fact canonica `inventory_positions`, calcolata dai movimenti di magazzino per articolo |
| [task/TASK-V2-038-giacenza-articoli-nel-dettaglio-ui.md](task/TASK-V2-038-giacenza-articoli-nel-dettaglio-ui.md) | Esposizione della giacenza calcolata nel dettaglio UI `articoli`, per validazione visiva del nuovo building block `inventory` |
| [task/TASK-V2-039-refresh-sequenziale-articoli-e-giacenza.md](task/TASK-V2-039-refresh-sequenziale-articoli-e-giacenza.md) | Primo refresh sequenziale backend-controlled della surface `articoli`, con orchestrazione `articoli -> mag_reale -> inventory_positions` |
| [task/TASK-V2-040-sync-righe-ordine-cliente.md](task/TASK-V2-040-sync-righe-ordine-cliente.md) | Mirror sync read-only di `V_TORDCLI` come base tecnica del futuro stream `ordini cliente` |
| [task/TASK-V2-041-core-ordini-cliente.md](task/TASK-V2-041-core-ordini-cliente.md) | Primo Core `ordini cliente`, con `customer_order_lines`, `description_lines` e `open_qty` calcolata |
| [task/TASK-V2-042-commitments-cliente.md](task/TASK-V2-042-commitments-cliente.md) | Primo computed fact `commitments` da provenienza `customer_order`, basato sul Core ordini cliente |
| [task/TASK-V2-043-commitments-produzione.md](task/TASK-V2-043-commitments-produzione.md) | Estensione di `commitments` alla provenienza `production`, limitata in V1 ai materiali con `CAT_ART1 != 0` |
| [task/TASK-V2-044-customer-set-aside.md](task/TASK-V2-044-customer-set-aside.md) | Computed fact `customer_set_aside` da `DOC_QTAP`, separato da `inventory` e `commitments` |
| [task/TASK-V2-045-set-aside-articoli-nel-dettaglio-ui.md](task/TASK-V2-045-set-aside-articoli-nel-dettaglio-ui.md) | Esposizione read-only del `customer_set_aside` nel dettaglio UI `articoli` |
| [task/TASK-V2-046-refresh-sequenziale-articoli-giacenza-e-set-aside.md](task/TASK-V2-046-refresh-sequenziale-articoli-giacenza-e-set-aside.md) | Estensione del refresh backend della surface `articoli` per ricalcolare anche `customer_set_aside` |
| [task/TASK-V2-047-refresh-articoli-con-ordini-per-set-aside.md](task/TASK-V2-047-refresh-articoli-con-ordini-per-set-aside.md) | Correzione del refresh `articoli` con `sync_righe_ordine_cliente` a monte del rebuild `customer_set_aside` |
| [task/TASK-V2-048-allineamento-operativo-righe-ordine-cliente.md](task/TASK-V2-048-allineamento-operativo-righe-ordine-cliente.md) | Correzione della sync ordini cliente per mantenerla allineata alle sole righe ancora presenti in `V_TORDCLI` |
| [task/TASK-V2-049-core-availability.md](task/TASK-V2-049-core-availability.md) | Computed fact `availability` come derivato di `inventory`, `customer_set_aside` e `commitments` |
| [task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md](task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md) | Esposizione read-only di `committed_qty` e `availability_qty` nel dettaglio UI `articoli` |
| [task/TASK-V2-051-refresh-sequenziale-articoli-con-availability.md](task/TASK-V2-051-refresh-sequenziale-articoli-con-availability.md) | Estensione del refresh backend della surface `articoli` per ricalcolare anche `availability` |
| [task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md](task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md) | Hardening leggero dei confronti `article_code` cross-source con helper condivisa `normalize_article_code` |
| [task/TASK-V2-053-refresh-sequenziale-articoli-con-commitments.md](task/TASK-V2-053-refresh-sequenziale-articoli-con-commitments.md) | Estensione del refresh backend della surface `articoli` per aggiornare anche `commitments` cliente e produzione |
| [task/TASK-V2-054-refresh-semantici-backend.md](task/TASK-V2-054-refresh-semantici-backend.md) | Refactor backend verso refresh semantici con dipendenze interne invece di catene tecniche replicate nei chiamanti |
| [task/TASK-V2-055-criticita-articoli-v1.md](task/TASK-V2-055-criticita-articoli-v1.md) | Prima vista operativa minima di `criticita articoli`, basata su una logica V1 semplice: articolo critico se `availability_qty < 0` |
| [task/TASK-V2-056-refinement-ui-criticita-articoli.md](task/TASK-V2-056-refinement-ui-criticita-articoli.md) | Refinement della vista `criticita articoli` con perimetro `considera_in_produzione`, filtro famiglia e ordinamenti per famiglia e campi quantitativi |
| [task/TASK-V2-057-toggle-considera-in-produzione-criticita.md](task/TASK-V2-057-toggle-considera-in-produzione-criticita.md) | Toggle del filtro `considera_in_produzione` nella vista `criticita articoli`, con default attivo e possibilita di disattivarlo per debug |
| [task/TASK-V2-058-refresh-criticita-collegato-a-refresh-articoli.md](task/TASK-V2-058-refresh-criticita-collegato-a-refresh-articoli.md) | Collegare il pulsante `Aggiorna` della vista `criticita articoli` al refresh semantico completo della surface `produzione/articoli` |
| [task/TASK-V2-059-hardening-criticita-join-article-code.md](task/TASK-V2-059-hardening-criticita-join-article-code.md) | Correggere le join cross-source della vista `criticita articoli` per allinearle alla chiave articolo canonica dei fact |
| [task/TASK-V2-060-perimetro-criticita-solo-articoli-presenti.md](task/TASK-V2-060-perimetro-criticita-solo-articoli-presenti.md) | Limitare la vista `criticita articoli` ai soli articoli presenti e attivi nella surface `articoli` |
| [task/TASK-V2-061-separazione-ricerca-codice-e-descrizione-articoli.md](task/TASK-V2-061-separazione-ricerca-codice-e-descrizione-articoli.md) | Separare nella vista `articoli` la ricerca per `codice` da quella per `descrizione`, mantenendo la normalizzazione dimensionale solo sul codice |
| [task/TASK-V2-062-core-planning-candidates-v1.md](task/TASK-V2-062-core-planning-candidates-v1.md) | Primo slice Core di `Planning Candidates` V1, customer-driven e aggregato per articolo, basato su `future_availability_qty` |
| [task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md](task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md) | Evolvere il modello `famiglia + articolo` per supportare planning policy con default di famiglia e override articolo |
| [task/TASK-V2-064-core-effective-planning-policy-articoli.md](task/TASK-V2-064-core-effective-planning-policy-articoli.md) | Esporre nel Core `articoli` i valori effettivi delle planning policy, risolti con precedenza override articolo > default famiglia |
| [task/TASK-V2-065-ui-planning-candidates-v1.md](task/TASK-V2-065-ui-planning-candidates-v1.md) | Prima surface UI di `Planning Candidates` V1, aggregata per articolo e coerente con i valori effettivi di planning policy |
| [task/TASK-V2-066-ui-planning-policy-famiglie.md](task/TASK-V2-066-ui-planning-policy-famiglie.md) | Estendere la UI `famiglie articolo` ai default di planning policy, incluso `aggrega_codice_in_produzione` |
| [task/TASK-V2-067-ui-override-e-effective-policy-articoli.md](task/TASK-V2-067-ui-override-e-effective-policy-articoli.md) | Introdurre nel dettaglio `articoli` la configurazione degli override e la lettura delle planning policy effettive |
| [task/TASK-V2-068-hardening-planning-candidates-escludi-completate.md](task/TASK-V2-068-hardening-planning-candidates-escludi-completate.md) | Hardening del Core `Planning Candidates` per escludere dall`incoming_supply_qty` le produzioni gia completate, anche via override |
| [task/TASK-V2-069-allineamento-nomenclatura-planning-mode.md](task/TASK-V2-069-allineamento-nomenclatura-planning-mode.md) | Allineare il vocabolario planning a `planning_mode`, preparando il branching V2 senza cambiare ancora il comportamento della V1 |
| [task/TASK-V2-070-ui-allineamento-nomenclatura-planning-mode.md](task/TASK-V2-070-ui-allineamento-nomenclatura-planning-mode.md) | Riallineare le schermate gia coinvolte dal planning al vocabolario esplicito `planning_mode`, senza cambiare ancora il comportamento delle surface |
| [task/TASK-V2-071-core-planning-candidates-v2-branching.md](task/TASK-V2-071-core-planning-candidates-v2-branching.md) | Evolvere il Core `Planning Candidates` dal modello V1 unico al branching reale tra modalita `by_article` e `by_customer_order_line` |
| [task/TASK-V2-072-ui-planning-candidates-v2-branching.md](task/TASK-V2-072-ui-planning-candidates-v2-branching.md) | Evolvere la UI `Planning Candidates` per rappresentare correttamente il branching reale tra candidate `by_article` e `by_customer_order_line` |
| [task/TASK-V2-073-fix-mag-reale-rebootstrap.md](task/TASK-V2-073-fix-mag-reale-rebootstrap.md) | Re-bootstrap completo di `sync_mag_reale` per eliminare movimenti fantasma e riallineare giacenza, availability e planning ai dati Easy corretti |
| [task/TASK-V2-074-core-planning-candidates-final-refinement.md](task/TASK-V2-074-core-planning-candidates-final-refinement.md) | Refinement finale del Core `Planning Candidates`: clamp stock a zero, reason esplicita, descrizione ordine e misura |
| [task/TASK-V2-075-ui-planning-candidates-final-refinement.md](task/TASK-V2-075-ui-planning-candidates-final-refinement.md) | Refinement finale della UI `Planning Candidates` per mostrare reason, misura e descrizione ordine nel ramo per-riga |
| [task/TASK-V2-076-core-warnings-v1.md](task/TASK-V2-076-core-warnings-v1.md) | Primo slice Core `Warnings` V1: warning canonici unici con `visible_to_areas` e tipi iniziali `NEGATIVE_STOCK` |
| [task/TASK-V2-077-admin-warning-visibility-config.md](task/TASK-V2-077-admin-warning-visibility-config.md) | Prima configurazione admin della warning visibility con `visible_to_areas` |
| [task/TASK-V2-078-ui-warnings-surface-v1.md](task/TASK-V2-078-ui-warnings-surface-v1.md) | Prima surface UI `Warnings` con lista canonici filtrata per area corrente |
| [task/TASK-V2-079-warning-badges-articoli-e-planning.md](task/TASK-V2-079-warning-badges-articoli-e-planning.md) | Badge warning in `articoli` e `Planning Candidates` — **deferred** |
| [task/TASK-V2-080-deprecazione-surface-criticita-articoli.md](task/TASK-V2-080-deprecazione-surface-criticita-articoli.md) | Deprecazione formale della surface `Criticita Articoli`, ancora presente tecnicamente |
| [task/TASK-V2-081-realign-warning-visibility-by-area.md](task/TASK-V2-081-realign-warning-visibility-by-area.md) | Riallineamento warning visibility al modello `visible_to_areas` definitivo |
| [task/TASK-V2-082-warnings-surface-filter-by-current-area.md](task/TASK-V2-082-warnings-surface-filter-by-current-area.md) | Filtro della surface `Warnings` per area corrente dell'utente, con bypass `admin` |
| [task/TASK-V2-083-model-stock-policy-defaults-and-overrides.md](task/TASK-V2-083-model-stock-policy-defaults-and-overrides.md) | Modello/config stock policy V1 con default famiglia e override articolo |
| [task/TASK-V2-084-core-stock-policy-metrics-v1.md](task/TASK-V2-084-core-stock-policy-metrics-v1.md) | Core stock policy metrics V1: `monthly_stock_base_qty`, `target_stock_qty`, `trigger_stock_qty` |
| [task/TASK-V2-085-planning-candidates-stock-driven-v1.md](task/TASK-V2-085-planning-candidates-stock-driven-v1.md) | Integrazione stock-driven nel ramo `by_article` di `Planning Candidates` con breakdown `customer_shortage_qty` / `stock_replenishment_qty` |
| [task/TASK-V2-086-stock-logic-config-and-strategy-selection.md](task/TASK-V2-086-stock-logic-config-and-strategy-selection.md) | Configurazione interna logiche stock con `strategy_key` selezionabile e parametri tunabili |
| [task/TASK-V2-087-hardening-monthly-stock-base-algorithm.md](task/TASK-V2-087-hardening-monthly-stock-base-algorithm.md) | Hardening algoritmo `monthly_stock_base_qty` con finestre multiple, percentile e filtro outlier |
| [task/TASK-V2-088-stock-policy-final-alignment-before-planning.md](task/TASK-V2-088-stock-policy-final-alignment-before-planning.md) | Allineamento finale stock policy V1 prima dell'integrazione planning |
| [task/TASK-V2-089-ui-articoli-stock-policy-metrics.md](task/TASK-V2-089-ui-articoli-stock-policy-metrics.md) | UI articoli per metriche e configurazioni stock policy |
| [task/TASK-V2-090-admin-stock-logic-config.md](task/TASK-V2-090-admin-stock-logic-config.md) | Configurazione admin delle logiche stock V1 |
| [task/TASK-V2-091-warning-invalid-stock-capacity.md](task/TASK-V2-091-warning-invalid-stock-capacity.md) | Nuovo warning canonico `INVALID_STOCK_CAPACITY` per articoli con stock policy ma capienza invalida |
| [task/TASK-V2-092-fix-capacity-from-containers-v1-legacy-formula.md](task/TASK-V2-092-fix-capacity-from-containers-v1-legacy-formula.md) | Fix formula `capacity_from_containers_v1` allineata alla formula legacy |
| [task/TASK-V2-093-ui-famiglie-stock-policy-defaults.md](task/TASK-V2-093-ui-famiglie-stock-policy-defaults.md) | UI famiglie per default stock policy |
| [task/TASK-V2-094-admin-stock-logic-dedicated-section-and-capacity-params.md](task/TASK-V2-094-admin-stock-logic-dedicated-section-and-capacity-params.md) | Refinement admin stock logic con sezione dedicata e parametri capacity |
| [task/TASK-V2-095-admin-stock-logic-separate-page.md](task/TASK-V2-095-admin-stock-logic-separate-page.md) | Pagina admin separata per la governance delle logiche stock |
| [task/TASK-V2-096-model-stock-policy-enabled-defaults-and-overrides.md](task/TASK-V2-096-model-stock-policy-enabled-defaults-and-overrides.md) | Modello/config per il flag esplicito `gestione_scorte_attiva` con default famiglia e override articolo |
| [task/TASK-V2-097-ui-famiglie-gestione-scorte-attiva.md](task/TASK-V2-097-ui-famiglie-gestione-scorte-attiva.md) | UI famiglie per la configurazione di `gestione_scorte_attiva` |
| [task/TASK-V2-098-ui-articoli-override-gestione-scorte-attiva.md](task/TASK-V2-098-ui-articoli-override-gestione-scorte-attiva.md) | UI articoli per override del flag `gestione_scorte_attiva` |
| [task/TASK-V2-099-core-stock-policy-and-planning-respect-enabled-flag.md](task/TASK-V2-099-core-stock-policy-and-planning-respect-enabled-flag.md) | Core planning e stock policy riallineati a `effective_gestione_scorte_attiva` |
| [task/TASK-V2-100-core-customer-horizon-planning-candidates.md](task/TASK-V2-100-core-customer-horizon-planning-candidates.md) | Flag `is_within_customer_horizon` nel Core `Planning Candidates` |
| [task/TASK-V2-101-core-stock-horizon-cap-on-commitments.md](task/TASK-V2-101-core-stock-horizon-cap-on-commitments.md) | Cap temporale sugli impegni della componente scorta basato su `stock horizon` |
| [task/TASK-V2-102-ui-planning-candidates-driver-filters-and-horizon.md](task/TASK-V2-102-ui-planning-candidates-driver-filters-and-horizon.md) | Filtri UI `Planning Candidates` per driver e customer horizon |
| [task/TASK-V2-103-core-separate-customer-and-stock-horizons.md](task/TASK-V2-103-core-separate-customer-and-stock-horizons.md) | Separazione Core tra `customer horizon` e `stock horizon` |
| [task/TASK-V2-104-ui-planning-customer-horizon-filter-semantic-fix.md](task/TASK-V2-104-ui-planning-customer-horizon-filter-semantic-fix.md) | Fix semantico UI/API del filtro `customer horizon` |
| [task/TASK-V2-105-planning-primary-driver-classification.md](task/TASK-V2-105-planning-primary-driver-classification.md) | Classificazione primaria `customer|stock` dei candidate `by_article` |
| [task/TASK-V2-106-required-qty-minimum-for-stock-only-candidates.md](task/TASK-V2-106-required-qty-minimum-for-stock-only-candidates.md) | `required_qty_minimum` coerente nei candidate `stock-only` |
| [task/TASK-V2-107-planning-candidates-requested-delivery-date.md](task/TASK-V2-107-planning-candidates-requested-delivery-date.md) | Data richiesta in `Planning Candidates` con semantica distinta tra riga ordine e ramo aggregato |
| [task/TASK-V2-108-core-planning-candidates-readability-contracts.md](task/TASK-V2-108-core-planning-candidates-readability-contracts.md) | Contratti Core planning per descrizione completa, destinazione richiesta e leggibilita |
| [task/TASK-V2-109-ui-planning-candidates-readability-refinement.md](task/TASK-V2-109-ui-planning-candidates-readability-refinement.md) | Refinement UI `Planning Candidates` per badge, misura, descrizioni e destinazioni |
| [task/TASK-V2-110-unify-planning-candidate-description-model.md](task/TASK-V2-110-unify-planning-candidate-description-model.md) | Modello descrittivo unificato con `description_parts` e `display_description` |
| [task/TASK-V2-111-core-planning-candidates-article-warnings-enrichment.md](task/TASK-V2-111-core-planning-candidates-article-warnings-enrichment.md) | Enrichment Core/API degli warning articolo in planning |
| [task/TASK-V2-112-ui-planning-candidates-warnings-column.md](task/TASK-V2-112-ui-planning-candidates-warnings-column.md) | Colonna `Warnings` nella tabella planning |
| [task/TASK-V2-113-ui-planning-candidates-article-quick-config-modal.md](task/TASK-V2-113-ui-planning-candidates-article-quick-config-modal.md) | Quick config modal articolo direttamente dalla vista planning |
| [task/TASK-V2-114-core-articoli-case-insensitive-code-bridge.md](task/TASK-V2-114-core-articoli-case-insensitive-code-bridge.md) | Bridge case-insensitive planning -> articoli per lookup e write config |
| [task/TASK-V2-115-core-proposal-export-preview-contracts.md](task/TASK-V2-115-core-proposal-export-preview-contracts.md) | Contratti Core per il preview export di `Production Proposals` |
| [task/TASK-V2-116-ui-production-proposals-export-preview-table.md](task/TASK-V2-116-ui-production-proposals-export-preview-table.md) | Tabella UI `Production Proposals` come preview dell'export |
| [task/TASK-V2-117-core-proposal-target-pieces-v1-logic.md](task/TASK-V2-117-core-proposal-target-pieces-v1-logic.md) | Logica proposal `proposal_target_pieces_v1` — baseline bundle `pieces` |
| [task/TASK-V2-118-model-raw-bar-length-enable-and-article-config.md](task/TASK-V2-118-model-raw-bar-length-enable-and-article-config.md) | Modello `raw_bar_length_mm` e configurazione articolo/famiglia |
| [task/TASK-V2-119-ui-famiglie-raw-bar-length-enable.md](task/TASK-V2-119-ui-famiglie-raw-bar-length-enable.md) | UI famiglie per abilitazione del campo `raw_bar_length_mm` |
| [task/TASK-V2-120-ui-articoli-raw-bar-length-mm-and-proposal-logic.md](task/TASK-V2-120-ui-articoli-raw-bar-length-mm-and-proposal-logic.md) | UI articoli per `raw_bar_length_mm` e assegnazione logica proposal |
| [task/TASK-V2-121-core-proposal-full-bar-v1-logic.md](task/TASK-V2-121-core-proposal-full-bar-v1-logic.md) | Logica proposal `proposal_full_bar_v1` — bundle `strict_capacity` con barra intera |
| [task/TASK-V2-122-warning-missing-raw-bar-length.md](task/TASK-V2-122-warning-missing-raw-bar-length.md) | Warning canonico `MISSING_RAW_BAR_LENGTH` per articoli con logica barra senza lunghezza grezzo |
| [task/TASK-V2-123-ui-articoli-hide-raw-bar-length-when-family-disabled.md](task/TASK-V2-123-ui-articoli-hide-raw-bar-length-when-family-disabled.md) | Nascondere `raw_bar_length_mm` nell'UI articoli quando la famiglia ha il flag disabilitato |
| [task/TASK-V2-124-core-proposal-logic-diagnostics.md](task/TASK-V2-124-core-proposal-logic-diagnostics.md) | Diagnostica locale `Production Proposals`: logica richiesta, effettiva e fallback reason |
| [task/TASK-V2-125-ui-production-proposals-logic-diagnostics.md](task/TASK-V2-125-ui-production-proposals-logic-diagnostics.md) | UI `Production Proposals` per mostrare la diagnostica logica proposal |
| [task/TASK-V2-126-realign-raw-bar-length-to-raw-material-articles.md](task/TASK-V2-126-realign-raw-bar-length-to-raw-material-articles.md) | Correzione ownership `raw_bar_length_mm` verso il materiale grezzo associato |
| [task/TASK-V2-127-core-proposal-full-bar-v2-capacity-floor-logic.md](task/TASK-V2-127-core-proposal-full-bar-v2-capacity-floor-logic.md) | Logica proposal `proposal_full_bar_v2_capacity_floor`: ceil, poi floor sotto capienza, poi fallback pezzi |
| [task/TASK-V2-128-core-planning-need-vs-release-now-contract.md](task/TASK-V2-128-core-planning-need-vs-release-now-contract.md) | Primo split `need vs release now` nel Core planning: `required_qty_eventual / release_qty_now_max / release_status` |
| [task/TASK-V2-129-ui-planning-need-vs-release-now-visibility.md](task/TASK-V2-129-ui-planning-need-vs-release-now-visibility.md) | Visibilita UI del contratto `need vs release now` |
| [task/TASK-V2-130-ui-admin-proposal-logic-two-column-governance.md](task/TASK-V2-130-ui-admin-proposal-logic-two-column-governance.md) | UI admin proposal logic a 2 colonne con governance suite e parametri |
| [task/TASK-V2-131-core-proposal-multi-bar-v1-logic.md](task/TASK-V2-131-core-proposal-multi-bar-v1-logic.md) | Logica proposal `proposal_multi_bar_v1_capacity_floor` |
| [task/TASK-V2-132-ui-articoli-proposal-logic-friendly-labels.md](task/TASK-V2-132-ui-articoli-proposal-logic-friendly-labels.md) | Label human-friendly per le logiche proposal nella UI articoli |
| [task/TASK-V2-133-ui-articoli-three-column-restructure.md](task/TASK-V2-133-ui-articoli-three-column-restructure.md) | Ristrutturazione UI articoli a 3 colonne |
| [task/TASK-V2-134-core-proposal-multi-bar-note-fragment-fasci.md](task/TASK-V2-134-core-proposal-multi-bar-note-fragment-fasci.md) | `note_fragment` dedicato `FASCI xN` per la logica proposal multi-bar — **aperto** |
| [task/TASK-V2-135-ui-warnings-root-navigation.md](task/TASK-V2-135-ui-warnings-root-navigation.md) | `Warnings` come modulo root di navigazione — **aperto** |
| [task/TASK-V2-136-ui-admin-unified-logic-config-three-column.md](task/TASK-V2-136-ui-admin-unified-logic-config-three-column.md) | Pagina admin unificata `Logic Config` a 3 colonne — **aperto** |
| [task/TASK-V2-137-ui-planning-unified-workspace-shadow-view-left-center.md](task/TASK-V2-137-ui-planning-unified-workspace-shadow-view-left-center.md) | Shadow view Planning Workspace con colonne sinistra e centrale |
| [task/TASK-V2-138-ui-planning-workspace-left-center-refinement.md](task/TASK-V2-138-ui-planning-workspace-left-center-refinement.md) | Refinement UI della colonna sinistra e centrale del Planning Workspace |
| [task/TASK-V2-139-ui-planning-workspace-filters-scope-customer-horizon-search.md](task/TASK-V2-139-ui-planning-workspace-filters-scope-customer-horizon-search.md) | Filtri workspace planning: scope, `Orizzonte cliente`, ricerche e sorting |
| [task/TASK-V2-140-ui-planning-workspace-calculation-params-and-right-config.md](task/TASK-V2-140-ui-planning-workspace-calculation-params-and-right-config.md) | Blocco `Parametri di calcolo` e scheda destra `Planning / Scorte` |
| [task/TASK-V2-141-ui-planning-workspace-calculation-params-compact-grid.md](task/TASK-V2-141-ui-planning-workspace-calculation-params-compact-grid.md) | Refinement wide-screen del blocco `Parametri di calcolo` in griglia compatta |
| [task/TASK-V2-142-core-planning-customer-horizon-coverage-test-case.md](task/TASK-V2-142-core-planning-customer-horizon-coverage-test-case.md) | Test Core su caso reale `12x8x25` per `customer horizon` e copertura |
| [task/TASK-V2-143-ui-planning-center-open-orders-and-stock-effective.md](task/TASK-V2-143-ui-planning-center-open-orders-and-stock-effective.md) | Ordini aperti e giacenza effettiva nella colonna centrale del Planning Workspace |
| [task/TASK-V2-144-ui-planning-center-show-order-block-also-for-stock-only.md](task/TASK-V2-144-ui-planning-center-show-order-block-also-for-stock-only.md) | Blocco `Cliente / Ordine` visibile anche nei candidate `stock-only` |
| [task/TASK-V2-145-core-planning-rebase-candidate-model-and-priority-score.md](task/TASK-V2-145-core-planning-rebase-candidate-model-and-priority-score.md) | Rebase Core planning: `customer_horizon` rimosso dal calcolo shortage e `priority_score` baseline V1 |
| [task/TASK-V2-146-docs-cleanup-and-archive-alignment.md](task/TASK-V2-146-docs-cleanup-and-archive-alignment.md) | Pulizia documentale e riallineamento degli indici al baseline rebase — **in corso** |
| [task/TASK-V2-147-ui-remove-legacy-criticality-navigation.md](task/TASK-V2-147-ui-remove-legacy-criticality-navigation.md) | Rimozione della surface legacy `Criticita` dalla navigazione primaria — **aperto** |
| [task/TASK-V2-148-legacy-compatibility-review-before-code-removal.md](task/TASK-V2-148-legacy-compatibility-review-before-code-removal.md) | Review delle compatibilita legacy prima del code cleanup — **aperto** |
| [task/TASK-V2-TEMPLATE.md](task/TASK-V2-TEMPLATE.md) | Template operativo per task di implementazione da affidare a Claude Code |

## Test

| File | Contenuto |
|------|-----------|
| [test/TEST-V2-001-task-pipeline-validation.md](test/TEST-V2-001-task-pipeline-validation.md) | Verifica del primo task backend e della pipeline AI -> task -> codice -> architettura |
| [test/TEST-V2-002-task-003-db-bootstrap-validation.md](test/TEST-V2-002-task-003-db-bootstrap-validation.md) | Verifica del bootstrap DB interno: modelli, migration, seed e bootstrap locale PostgreSQL |
| [test/TEST-V2-003-task-004-browser-auth-validation.md](test/TEST-V2-003-task-004-browser-auth-validation.md) | Verifica del login browser, payload di sessione e build frontend della V2 |

## Archive

La cartella `archive/` contiene documenti V2 non attivi o superseded, anch'essi organizzati per tipo quando utile.
