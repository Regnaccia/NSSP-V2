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
| [decisions/ARCH/DL-ARCH-V2-TEMPLATE.md](decisions/ARCH/DL-ARCH-V2-TEMPLATE.md) | Template minimo per nuovi Decision Log architetturali V2 |
| [decisions/UIX/DL-UIX-V2-001.md](decisions/UIX/DL-UIX-V2-001.md) | Modello UI di navigazione multi-surface con layout persistente e sidebar basata su `available_surfaces` |
| [decisions/UIX/DL-UIX-V2-002.md](decisions/UIX/DL-UIX-V2-002.md) | Target UI della surface logistica clienti/destinazioni con layout persistente a 3 colonne |
| [decisions/UIX/DL-UIX-V2-003.md](decisions/UIX/DL-UIX-V2-003.md) | Navigazione contestuale per-surface: livello primario per le surface e livello secondario per le funzioni interne della surface attiva |

## Guides

| File | Contenuto |
|------|-----------|
| [guides/BACKEND_BOOTSTRAP_AND_VERIFY.md](guides/BACKEND_BOOTSTRAP_AND_VERIFY.md) | Bootstrap locale backend/frontend, auth browser, admin e sync Easy read-only per clienti e destinazioni |

## Integrations

| File | Contenuto |
|------|-----------|
| [integrations/README.md](integrations/README.md) | Indice della documentazione tecnica per le integrazioni esterne V2 |
| [integrations/easy/README.md](integrations/easy/README.md) | Documentazione tecnica delle entita Easy lette in read-only |
| [integrations/easy/catalog/README.md](integrations/easy/catalog/README.md) | Catalogo machine-generated degli schemi Easy in formato JSON |
| [integrations/easy/EASY_CLIENTI.md](integrations/easy/EASY_CLIENTI.md) | Mapping curato della tabella `ANACLI` verso il target interno `sync_clienti` |
| [integrations/easy/EASY_DESTINAZIONI.md](integrations/easy/EASY_DESTINAZIONI.md) | Mapping curato della tabella `POT_DESTDIV` verso il target interno `sync_destinazioni` |
| [integrations/easy/EASY_ENTITY_MAPPING_TEMPLATE.md](integrations/easy/EASY_ENTITY_MAPPING_TEMPLATE.md) | Template per documentare una mappatura Easy verso il target sync interno V2 |

## Roadmap

La cartella `roadmap/` resta attiva per futuri documenti roadmap realmente V2.

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
| [task/TASK-V2-TEMPLATE.md](task/TASK-V2-TEMPLATE.md) | Template operativo per task di implementazione da affidare a Claude Code |

## Test

| File | Contenuto |
|------|-----------|
| [test/TEST-V2-001-task-pipeline-validation.md](test/TEST-V2-001-task-pipeline-validation.md) | Verifica del primo task backend e della pipeline AI -> task -> codice -> architettura |
| [test/TEST-V2-002-task-003-db-bootstrap-validation.md](test/TEST-V2-002-task-003-db-bootstrap-validation.md) | Verifica del bootstrap DB interno: modelli, migration, seed e bootstrap locale PostgreSQL |
| [test/TEST-V2-003-task-004-browser-auth-validation.md](test/TEST-V2-003-task-004-browser-auth-validation.md) | Verifica del login browser, payload di sessione e build frontend della V2 |

## Archive

La cartella `archive/` contiene documenti V2 non attivi o superseded, anch'essi organizzati per tipo quando utile.
