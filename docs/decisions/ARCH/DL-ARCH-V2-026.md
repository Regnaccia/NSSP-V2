# DL-ARCH-V2-026 - Planning policy di default a livello famiglia con override articolo

## Status
Accepted

## Date
2026-04-10

## Context

Con `DL-ARCH-V2-025` la V2 ha definito la V1 di `Planning Candidates` come modulo:

- `customer-driven`
- aggregato per `article`
- basato su `future_availability_qty`

Ma restano ancora aperti alcuni temi strutturali che non vanno risolti con hardcode locali:

- quali articoli devono entrare nel perimetro delle logiche operative di planning
- quando un articolo puo essere aggregato per codice
- come gestire le eccezioni senza moltiplicare inutilmente le famiglie articolo

La V2 dispone gia di:

- `famiglia articolo` come classificazione interna
- flag `considera_in_produzione` a livello famiglia
- configurazione articolo -> famiglia

Il flag `considera_in_produzione` e nato inizialmente come supporto operativo per slice semplici come `criticita articoli`, ma con l'introduzione dei moduli di planning diventa necessario dargli un significato piu generale e stabile.

Serve quindi una regola esplicita per governare le future policy operative:

- con default a livello famiglia
- con override puntuale a livello articolo

senza costringere la famiglia a rappresentare eccezioni isolate.

## Decision

Le policy operative rilevanti per il planning sono definite con questo modello:

- default a livello `famiglia articolo`
- override puntuale a livello `articolo`
- precedenza: `override articolo` > `default famiglia`

La famiglia resta il luogo naturale per esprimere la regola generale.
L'articolo gestisce i casi eccezionali.

## Core Rule

La V2 adotta il principio:

> Le policy operative di planning devono nascere come default di famiglia e poter essere sovrascritte per singolo articolo quando il comportamento reale del singolo item si discosta dalla regola generale.

Conseguenza:

- la famiglia non deve essere duplicata o frammentata solo per modellare eccezioni
- le eccezioni devono preferibilmente vivere come override articolo

## Planning Policy Model

La planning policy effettiva di un articolo non viene letta direttamente da un solo campo.

Viene risolta tramite una funzione logica equivalente a:

```text
effective_planning_policy(article) =
  article_override if article_override is set
  else family_default
```

Questa regola vale per ogni futura policy di planning che abbia senso a entrambi i livelli.

## 1. Riposizionamento di `considera_in_produzione`

Il flag `considera_in_produzione` viene reinterpretato come:

- default di famiglia per l'inclusione dell'articolo nelle logiche operative di planning/produzione

Non e piu solo un filtro locale della vista `criticita`.

Nuovo significato architetturale:

- se `true`, la famiglia indica che gli articoli di quella famiglia entrano per default nelle logiche operative orientate a produzione/planning
- se `false`, gli articoli della famiglia restano fuori per default da quelle logiche, salvo override articolo

Impatto:

- `criticita articoli` puo continuare a riusare questo segnale
- i futuri moduli di planning possono basarsi sullo stesso concetto senza introdurre un secondo flag equivalente

## 2. Nuovo flag di default: `aggrega_codice_in_produzione`

La V2 introduce il concetto di:

- `aggrega_codice_in_produzione`

come flag di planning policy.

Significato:

- se `true`, l'articolo puo essere trattato per default come aggregabile a livello codice nelle logiche operative di produzione/planning
- se `false`, l'articolo non deve essere aggregato automaticamente per codice senza una logica piu specifica

Nel breve termine questo flag prepara i futuri step su:

- `Planning Candidates`
- politiche di aggregazione
- distinzione futura tra casi aggregabili e non aggregabili

## 3. Override articolo

Le policy sopra devono poter esistere anche a livello articolo come override puntuale.

Forma raccomandata:

- campo nullable / tri-state a livello articolo

Comportamento:

- `null` -> eredita dalla famiglia
- valore esplicito -> sovrascrive la policy della famiglia

Questo pattern va preferito a:

- creare nuove famiglie solo per una singola eccezione
- hardcodare eccezioni nella logica del modulo

## 4. Effective policy

Per ogni articolo, la V2 deve poter esporre una policy effettiva almeno per:

- inclusione nel perimetro planning
- aggregazione per codice

Quindi, a livello logico:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`

Questi valori effettivi sono quelli che devono essere consumati dai moduli operativi futuri.

## Relationship With Existing Decisions

Questo DL non sostituisce:

- `DL-ARCH-V2-014` su `famiglia articolo`
- `DL-ARCH-V2-023` sulle logiche intercambiabili
- `DL-ARCH-V2-025` sulla V1 ridotta di `Planning Candidates`

Li estende:

- `DL-ARCH-V2-014` definisce la famiglia come classificazione interna stabile
- questo DL definisce come la famiglia diventa portatrice di default operativi
- `DL-ARCH-V2-025` puo quindi restare semplice oggi, lasciando alle policy future una base esplicita

## Consequences

### Positive

- evita la proliferazione di famiglie usate solo per eccezioni
- introduce una linea chiara per le future policy di planning
- rende riusabile `considera_in_produzione` come concetto piu generale
- prepara l'introduzione controllata di `aggregable / non_aggregable`
- mantiene il modello espandibile senza hardcode diffusi

### Negative

- aumenta il ruolo del Core `articoli` come contenitore di configurazioni operative
- richiede futura UI/configurazione per gli override articolo
- obbliga i moduli futuri a risolvere sempre la policy effettiva, non solo a leggere la famiglia

## Out of Scope

Questo DL non impone ancora:

- la migrazione immediata del database o dei read model esistenti
- la UI di override articolo
- il naming fisico definitivo dei campi DB
- la modifica immediata della logica `Planning Candidates` V1 gia in corso

Fissa la regola architetturale e la direzione dei prossimi task.

## References

- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`
- `docs/task/TASK-V2-062-core-planning-candidates-v1.md`
