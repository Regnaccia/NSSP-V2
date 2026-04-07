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
| [decisions/ARCH/DL-ARCH-V2-TEMPLATE.md](decisions/ARCH/DL-ARCH-V2-TEMPLATE.md) | Template minimo per nuovi Decision Log architetturali V2 |
| [decisions/UIX/DL-UIX-V2-001.md](decisions/UIX/DL-UIX-V2-001.md) | Modello UI di navigazione multi-surface con layout persistente e sidebar basata su `available_surfaces` |

## Guides

| File | Contenuto |
|------|-----------|
| [guides/BACKEND_BOOTSTRAP_AND_VERIFY.md](guides/BACKEND_BOOTSTRAP_AND_VERIFY.md) | Bootstrap locale backend/frontend, auth browser e verifica tecnica del setup V2 |

## Integrations

| File | Contenuto |
|------|-----------|
| [integrations/README.md](integrations/README.md) | Indice della documentazione tecnica per le integrazioni esterne V2 |
| [integrations/easy/README.md](integrations/easy/README.md) | Documentazione tecnica delle entita Easy lette in read-only |
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
| [task/TASK-V2-007-bootstrap-sync-clienti.md](task/TASK-V2-007-bootstrap-sync-clienti.md) | Primo slice tecnico del layer sync: sync unit `clienti`, target interno, run metadata minimi e verifica di idempotenza |
| [task/TASK-V2-TEMPLATE.md](task/TASK-V2-TEMPLATE.md) | Template operativo per task di implementazione da affidare a Claude Code |

## Test

| File | Contenuto |
|------|-----------|
| [test/TEST-V2-001-task-pipeline-validation.md](test/TEST-V2-001-task-pipeline-validation.md) | Verifica del primo task backend e della pipeline AI -> task -> codice -> architettura |
| [test/TEST-V2-002-task-003-db-bootstrap-validation.md](test/TEST-V2-002-task-003-db-bootstrap-validation.md) | Verifica del bootstrap DB interno: modelli, migration, seed e bootstrap locale PostgreSQL |
| [test/TEST-V2-003-task-004-browser-auth-validation.md](test/TEST-V2-003-task-004-browser-auth-validation.md) | Verifica del login browser, payload di sessione e build frontend della V2 |

## Archive

La cartella `archive/` contiene documenti V2 non attivi o superseded, anch'essi organizzati per tipo quando utile.
