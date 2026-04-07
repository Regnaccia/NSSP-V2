# ODE Documentation

## Struttura

```text
docs/
├── archive/          documenti V2 non attivi o superseded
├── charter/          scopo, principi e criteri guida della V2
├── decisions/        decision log V2 organizzati per tipo
├── guides/           guide operative e convenzioni V2
├── roadmap/          sviluppi confermati e punti aperti della V2
├── task/             task di implementazione passati a Claude Code
└── test/             report di verifica su task, pipeline e controlli manuali
```

## Charter

| File | Contenuto |
|------|-----------|
| [charter/V2_CHARTER.md](charter/V2_CHARTER.md) | Charter principale della V2 |

## Decisions

Sottocartelle per tipo:

- `ARCH/`
- `OPS/`

| File | Contenuto |
|------|-----------|
| [decisions/ARCH/DL-ARCH-V2-001.md](decisions/ARCH/DL-ARCH-V2-001.md) | Struttura repository V2 e confini espliciti tra sync, core e app |
| [decisions/ARCH/DL-ARCH-V2-002.md](decisions/ARCH/DL-ARCH-V2-002.md) | Verifica riproducibile dei task e completion contract |
| [decisions/ARCH/DL-ARCH-V2-003.md](decisions/ARCH/DL-ARCH-V2-003.md) | Modello di accesso utente, ruoli e canali client |
| [decisions/ARCH/DL-ARCH-V2-TEMPLATE.md](decisions/ARCH/DL-ARCH-V2-TEMPLATE.md) | Template minimo per nuovi Decision Log architetturali V2 |

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
| [task/TASK-V2-TEMPLATE.md](task/TASK-V2-TEMPLATE.md) | Template operativo per task di implementazione da affidare a Claude Code |

## Test

| File | Contenuto |
|------|-----------|
| [test/TEST-V2-001-task-pipeline-validation.md](test/TEST-V2-001-task-pipeline-validation.md) | Verifica del primo task backend e della pipeline AI -> task -> codice -> architettura |

## Archive

La cartella `archive/` contiene documenti V2 non attivi o superseded, anch'essi organizzati per tipo quando utile.

## Guides

La cartella `guides/` e pronta per convenzioni e guide operative specifiche della V2.
