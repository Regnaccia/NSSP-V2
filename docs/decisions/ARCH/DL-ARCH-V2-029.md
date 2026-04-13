# DL-ARCH-V2-029 - Warnings come modulo trasversale canonico

## Status

Accepted

## Date

2026-04-13

## Context

La V2 ha gia separato il bisogno produttivo dalle anomalie inventariali nel modulo `Planning Candidates`.

In particolare:

- stock negativo non deve generare automaticamente un candidate
- resta pero un'anomalia importante che il sistema deve poter rendere visibile

In futuro potranno esistere warning:

- trasversali a piu reparti
- rilevanti per un solo reparto
- visibili solo in certe surface

Serve quindi una regola architetturale unica per evitare duplicazioni di warning tra moduli o reparti, chiarendo anche come la surface dedicata `Warnings` debba applicare la visibilita.

## Decision

### 1. Modulo unico e trasversale

`Warnings` viene adottato come modulo trasversale unico.

Non esistono warning distinti per reparto come oggetti separati.

Esiste un solo warning canonico che puo essere consumato da piu moduli o surface.

### 2. Un warning esiste una sola volta

Regola:

- il warning viene generato e posseduto dal modulo `Warnings`
- gli altri moduli possono solo leggerlo o proiettarlo

Questo evita:

- duplicazione della stessa anomalia in piu modelli
- divergenze di stato tra warning "di produzione" e warning "di magazzino"

### 3. Visibilita basata su audience, non su duplicazione

La rilevanza per reparto o surface viene modellata tramite metadati di audience, per esempio:

- `visible_to_areas`
- `visible_to_roles`
- `domain_tags`

La semantica target e per area/reparto operativo, non per singola surface applicativa.

Esempi di aree:

- `magazzino`
- `produzione`
- `logistica`

La configurazione di questi metadati di visibilita e considerata dato interno V2 e deve essere governabile dalla surface `admin`.

La surface `Warnings` resta consultabile come punto trasversale unico e non deve richiedere una configurazione warning-by-warning per essere raggiungibile.

La lista warning mostrata nella surface `Warnings`, pero, non e globale:

- deve essere filtrata in base all'area/reparto corrente
- ogni area vede solo i warning che la includono in `visible_to_areas`
- la configurazione `visible_to_areas` governa sia i consumi nei moduli operativi sia il contenuto della surface `Warnings`

### 4. Primo warning in scope

Il primo tipo di warning adottato e:

- `NEGATIVE_STOCK`

Definizione:

- articolo con `stock_calculated < 0`

Regola:

- `NEGATIVE_STOCK` non e un need produttivo
- non genera automaticamente produzione
- puo essere visibile in piu surface operative

### 5. Ownership esplicita

Il warning appartiene al modulo `Warnings`, non al modulo che lo mostra.

Conseguenze:

- `Planning Candidates` puo mostrare badge o indicatori warning
- `articoli` puo mostrare warning collegati all'articolo
- future viste di magazzino o produzione possono consumare lo stesso warning
- la surface `Warnings` puo mostrare lo stesso warning a piu aree, ma sempre filtrando per audience

Ma la logica di generazione e persistenza resta centralizzata.

### 6. Governance amministrativa

Le regole di visibilita dei warning non vengono delegate ai singoli moduli operativi.

La loro configurazione deve essere accessibile da `admin`, che resta il punto di governo trasversale per:

- audience per ruolo
- audience per area/reparto
- future regole di classificazione o dominio

## Consequences

### Positive

- separazione piu netta tra anomaly detection e decision logic
- warning coerenti e non duplicati
- maggiore riusabilita cross-surface
- base solida per workflow warning futuri

### Tradeoffs

- richiede un piccolo layer in piu invece di warning locali sparsi nei moduli
- la visibilita per ruolo/surface va progettata bene fin dal primo slice

## Out of Scope

- workflow completo `open / acknowledged / resolved`
- note operatore obbligatorie
- tassonomia completa di tutti i warning futuri
- UI finale del modulo warnings

## References

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`
