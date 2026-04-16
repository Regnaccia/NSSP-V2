# ODE V2 - Rebase Backlog 2026-04-15

## Scopo

Questo documento traduce in backlog operativo il `rebase` architetturale fissato da:

- `docs/reviews/PROJECT_REVIEW_2026-04-15_GENERAL.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`

La regola da questo punto in avanti e:

- non si continua il progetto per micro-fix locali isolati
- si usano i task futuri solo se coerenti con il baseline del rebase

## Stream attivi

### 1. Domain Rebase

Stream prioritario.

Ordine raccomandato:

1. baseline architetturale fissata
2. rebase del contratto `Planning Candidates`
3. rebase del contratto `Production Proposals`
4. riallineamento esplicito del backlog per stream e ownership

Output attesi:

- distinzione chiara `need vs release now`
- logiche proposal ripensate come bundle di policy
- ownership dati stabile tra finito, grezzo, famiglia e admin

### 2. Backbone Hardening

Stream parallelo ma non da mischiare con il rebase di dominio.

Backlog minimo:

- strategia strutturale `MAG_REALE`
- refresh fail-fast e freshness
- gestione orfani `core_articolo_config`

## Reclassificazione del cluster proposal 115-127

Il cluster `115-127` non e piu da leggere come sequenza di lavoro lineare.

Tutti i task risultano gia chiusi a livello implementativo, ma vanno reinterpretati nel modello post-rebase.

| Task | Stato reale | Classificazione post-rebase | Nota |
|------|-------------|-----------------------------|------|
| `TASK-V2-115` | Completed | Still valid unchanged | Il contratto export-preview resta valido e va preservato. |
| `TASK-V2-116` | Completed | Still valid unchanged | La tabella proposal come preview export resta corretta. |
| `TASK-V2-117` | Completed | Valid but dependent on new contracts | Resta la baseline del bundle `pieces`, non il modello finale delle logiche. |
| `TASK-V2-118` | Completed | Valid but dependent on new contracts | Va letto dentro l'ownership corretta finito/grezzo/famiglia. |
| `TASK-V2-119` | Completed | Still valid unchanged | Il flag famiglia resta coerente se usato come eligibility del grezzo. |
| `TASK-V2-120` | Completed | Valid but dependent on new contracts | La UI articoli resta utile, ma va governata dal modello di ownership post-rebase. |
| `TASK-V2-121` | Completed | Valid but dependent on new contracts | `proposal_full_bar_v1` resta una compatibility slice della policy `strict_capacity`. |
| `TASK-V2-122` | Completed | Still valid unchanged | `MISSING_RAW_BAR_LENGTH` resta warning canonico e non locale a proposal. |
| `TASK-V2-123` | Completed | Still valid unchanged | Il comportamento UI resta valido. |
| `TASK-V2-124` | Completed | Still valid unchanged | La diagnostica locale proposal requested/effective/fallback va preservata. |
| `TASK-V2-125` | Completed | Still valid unchanged | La UI della diagnostica proposal resta valida. |
| `TASK-V2-126` | Completed | Merged into larger slice | La correzione grezzo vs finito e ormai parte del contratto di ownership, non un refinement isolato. |
| `TASK-V2-127` | Completed | Valid but dependent on new contracts | `capacity_floor` resta una compatibility slice della futura `proposal_capacity_policy`. |

## Regole di lettura del backlog da ora

### Planning

Ogni nuovo task planning deve dichiarare esplicitamente se modifica:

- `need detection`
- `release feasibility`
- oppure solo la presentazione/readability

Non sono piu ammessi task che parlano genericamente di "quantita planning" senza dire quale semantica stanno toccando.

### Proposal

Ogni nuovo task proposal deve dichiarare esplicitamente se modifica:

- `proposal_base_qty_policy`
- `proposal_lot_policy`
- `proposal_capacity_policy`
- `proposal_customer_guardrail_policy`
- `proposal_note_policy`
- oppure solo la compatibility surface `proposal_logic_key`

Non sono piu ammessi task che introducono nuove `proposal_*_vN` senza spiegare su quale asse di policy intervengono.

### Warnings e diagnostica

Ogni nuovo task deve classificare l'output come:

- warning canonico cross-module
- diagnostica locale del modulo

## Prossimo stream corretto

La sequenza corretta da questo punto in avanti e:

1. fissare il contratto `Planning Candidates` con split `required_qty_eventual / release_qty_now_max / release_status`
2. fissare il contratto proposal in termini di policy bundle
3. solo dopo aprire nuovi task implementativi sui comportamenti quantitativi

Il `backbone hardening` non va mescolato dentro i task planning/proposal salvo dipendenza tecnica esplicita.
