# DL-ARCH-V2-023 - Logiche di dominio come funzioni intercambiabili su fact canonici

## Status

Accepted

## Date

2026-04-09

## Context

La V2 ha ormai costruito un primo set stabile di fact canonici nel `core`, in particolare:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

Fin qui il lavoro si e concentrato soprattutto su:

- mirror `sync`
- computed fact canonici
- read model e UI di validazione

Con l'evoluzione verso superfici operative e decisioni di dominio, il progetto entra in una fase diversa:

- non basta piu esporre numeri
- serve applicare logiche valutative sui fact
- queste logiche dovranno evolvere nel tempo

Esempio immediato:

- V1 `articolo critico` se `availability_qty < 0`
- V2 `articolo critico` se `availability_qty < safety_stock`
- V3 `articolo critico` con regole piu ricche, priorita o soglie diverse

Se queste logiche vengono hardcodate direttamente:

- nei router
- nei read model
- nei componenti UI
- nei rebuild dei fact canonici

ogni evoluzione futura rischia di:

- rompere il modello
- duplicare formule
- rendere difficile testare e confrontare logiche diverse

## Decision

Le logiche di dominio che interpretano fact canonici devono essere modellate come **funzioni intercambiabili**, non come formule hardcoded sparse nel sistema.

La separazione corretta e:

- `fact canonici`
  - dati stabili e riusabili
- `logic function`
  - funzione pura o quasi-pura che interpreta i fact
- `projection / read model`
  - esposizione dell'esito della logica a UI o API

## Regole

### Regola 1 - I fact canonici restano stabili

I fact canonici non devono cambiare semantica ogni volta che cambia una logica operativa.

Esempi:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

restano building block autonomi e riusabili.

### Regola 2 - La logica e un livello separato

La valutazione di dominio deve vivere in una funzione dedicata che riceve un contesto stabile e restituisce un esito esplicito.

Esempio astratto:

- input: `ArticleLogicContext`
- output: `ArticleCriticalityResult`

### Regola 3 - Le implementazioni devono essere sostituibili

Il sistema deve poter passare da una logica a un'altra senza riscrivere:

- i fact canonici
- il modello dati di base
- la UI che consuma l'esito

Questo non richiede un plugin system complesso.

Per la V2 e sufficiente una struttura in cui:

- esiste una interfaccia o funzione stabile
- esiste una implementazione attiva V1
- in futuro si puo sostituire l'implementazione o introdurre una policy diversa

### Regola 4 - La UI consuma esiti, non formule hardcoded

La UI non deve calcolare direttamente la logica di dominio a partire dai fact grezzi.

La UI deve leggere:

- stato
- reason
- eventuali valori di supporto

dal `core` o da un read model applicativo dedicato.

### Regola 5 - Le logiche devono essere testabili in isolamento

Ogni logica operativa deve poter essere verificata con test mirati sul solo contesto di input e sull'esito atteso, senza dipendere da tutta la chain di sync o UI.

## Initial Application

La prima applicazione prevista di questo pattern e:

- `criticita articoli`
- oppure `stato_copertura_articolo`

basata inizialmente su:

- `availability_qty`

con una prima logica molto stretta, ad esempio:

- `critical` se `availability_qty < 0`

e con possibilita futura di introdurre:

- `safety_stock`
- soglie diverse per famiglia
- criteri temporali o operativi aggiuntivi

## Consequences

### Positive

- logiche piu facili da testare
- minore coupling tra modello e formula operativa
- evoluzione graduale delle regole senza riscrivere i fact
- UI piu stabile

### Negative

- un livello logico in piu da modellare
- necessita di chiarire bene input e output delle logiche
- rischio di over-engineering se applicato a casi troppo piccoli

## Out of Scope

Questo DL non introduce ancora:

- la logica concreta di `criticita articoli`
- una surface dedicata alle criticita
- safety stock
- ATP
- motore di regole configurabile da UI

## Related

- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
