# DL-ARCH-V2-024 - Distinzione tra chiave articolo raw e chiave articolo canonica

## Status
Accepted

## Date
2026-04-10

## Context

Con l'introduzione dei fact canonici cross-source:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`
- prime proiezioni logiche come `criticita`

il progetto usa sempre piu spesso il codice articolo come chiave di join tra:

- mirror `sync_*`
- tabelle Core
- read model
- logiche di dominio

Nel dominio reale il codice articolo non distingue entita diverse in base al solo `upper/lower case`, ma i dati provenienti dalle sorgenti o dalle configurazioni interne possono comunque comparire in forma raw diversa dalla chiave canonica usata dai fact.

Questo crea un rischio strutturale:

- stessa entita logica con chiavi tecniche diverse
- join parziali o fallite tra fact canonici e dati raw
- proiezioni che non vedono arricchimenti o configurazioni esistenti

Il bug emerso sulla vista `criticita articoli` e un esempio tipico di questo problema.

## Decision

La V2 adotta esplicitamente due livelli distinti di chiave articolo:

### 1. Raw article key

La `raw article key`:

- preserva il valore vicino alla sorgente o al contesto di input
- serve per:
  - tracciabilita
  - audit
  - source identity
  - round-trip verso Easy

Non deve essere usata come chiave logica cross-source nei fact canonici o nelle logiche di dominio.

### 2. Canonical article key

La `canonical article key`:

- deriva sempre da `normalize_article_code`
- serve per:
  - join cross-source
  - fact canonici
  - read model derivati da piu sorgenti
  - logiche di dominio
  - proiezioni applicative che uniscono dati eterogenei

Questa e la chiave logica stabile del dominio articolo.

## Regole

### Regola 1 - I fact canonici usano solo la chiave canonica

Tutti i fact canonici del Core che rappresentano stato o derivazioni multi-sorgente devono usare la chiave articolo canonica.

Esempi:

- `inventory_positions`
- `customer_set_aside`
- `commitments`
- `availability`

### Regola 2 - I mirror possono mantenere la chiave raw

I mirror `sync_*` possono mantenere la chiave raw o source-facing, se questo li rende piu aderenti alla sorgente.

La semantica del mirror non va forzata solo per allinearsi ai fact canonici.

### Regola 3 - Vietato joinare direttamente canonico e raw

Non si deve fare join diretto tra:

- una chiave canonica
- una chiave raw

senza una normalizzazione esplicita o un campo canonico equivalente.

Questa regola vale per:

- query Core
- read model
- projection logic
- slice applicativi

### Regola 4 - Le logiche di dominio consumano chiavi canoniche

Le logiche di dominio introdotte sotto `DL-ARCH-V2-023` devono lavorare su contesti che usano chiavi canoniche, non chiavi raw.

### Regola 5 - Se una tabella interna partecipa a join cross-source, deve chiarire quale chiave espone

Per ogni nuova tabella interna che puo essere:

- sorgente di arricchimento
- punto di join con fact canonici
- supporto a read model multi-sorgente

va chiarito esplicitamente se conserva:

- solo chiave raw
- solo chiave canonica
- entrambe

Se conserva entrambe, i ruoli devono essere distinti.

## Consequences

### Positive

- riduzione dei mismatch tra fact canonici e dati di arricchimento
- logiche di dominio piu stabili
- maggiore chiarezza tra tracciabilita sorgente e chiave logica di dominio
- minore rischio di bug nelle proiezioni UI o nei read model

### Negative

- maggiore disciplina richiesta nei join
- possibile necessita futura di aggiungere campi canonici a tabelle oggi raw-oriented
- alcune query esistenti vanno corrette o hardenizzate

## Implementation Guidance

- usare `normalize_article_code` come unico punto di definizione della canonicalizzazione
- mantenere i mirror vicini alla sorgente salvo esigenze esplicite diverse
- nei read model multi-sorgente preferire:
  - campi canonici persistiti
  - oppure join che esplicitano la normalizzazione
- evitare nuove helper locali duplicate della stessa regola

## Out of Scope

Questo DL non impone:

- refactor immediato di tutti i mirror per aggiungere una chiave canonica persistita
- riscrittura completa delle tabelle esistenti
- un unico naming fisico obbligatorio dei campi nel database

Fissa la regola architetturale da seguire nei task futuri e negli hardening progressivi.

## References

- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md`
- `docs/task/TASK-V2-059-hardening-criticita-join-article-code.md`
