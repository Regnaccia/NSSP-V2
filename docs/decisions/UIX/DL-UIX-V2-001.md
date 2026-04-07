# DL-UIX-V2-001 - Navigazione applicativa multi-surface

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 supporta utenti con uno o piu ruoli contemporaneamente.

I DL architetturali gia attivi hanno fissato che:

- l'utente autenticato espone `roles[]`
- il backend espone `available_surfaces`
- una `surface` e un'area funzionale applicativa, non un ruolo e non una singola pagina

L'approccio iniziale basato su chooser post-login ha avuto valore come primo slice,
ma presenta limiti evidenti quando un utente puo accedere a piu surface nello stesso sistema:

- costringe l'utente a trattare il login come meccanismo di navigazione
- rende scomodo il passaggio tra aree applicative autorizzate
- accoppia troppo il flusso post-login a una scelta iniziale obbligatoria

Con l'introduzione delle prime surface reali, la V2 ha bisogno di un pattern UI stabile che:

- separi autenticazione da navigazione applicativa
- consenta la navigazione tra piu surface autorizzate nella stessa sessione
- resti coerente con il contratto backend gia definito

## Decision

La V2 adotta un modello di navigazione applicativa basato su:

- layout persistente condiviso
- sidebar come entry point principale della navigazione
- navigazione interna tra surface autorizzate
- superamento del chooser post-login come flusso standard

### 1. Sessione unica, piu surface accessibili

Una sessione autenticata rappresenta:

- un utente
- un insieme di ruoli
- un insieme di surface accessibili

La sessione non e limitata a una sola surface.

### 2. Sidebar come pattern di navigazione primario

L'interfaccia principale include una sidebar persistente che:

- elenca le surface disponibili per l'utente
- consente il passaggio tra surface senza nuovo login
- resta coerente con il layout comune dell'applicazione

La sidebar e un pattern UI globale, non una soluzione ad hoc per una singola surface.

### 3. Le voci di navigazione derivano da `available_surfaces`

Le voci principali della sidebar non sono derivate direttamente dai ruoli grezzi,
ma dal contratto di sessione esposto dal backend.

Regola:

- backend: decide `available_surfaces`
- frontend: costruisce sidebar, redirect e discoverability a partire da `available_surfaces`

Questo mantiene pulita la distinzione tra:

- ruolo
- surface
- route/page

### 4. Routing iniziale post-login

Dopo il login:

- se e disponibile una sola surface primaria, il frontend fa redirect automatico
- se sono disponibili piu surface, il frontend apre una surface di default coerente con la sessione

Il chooser iniziale non e piu il flusso standard.

Puo restare solo come fallback tecnico temporaneo durante la transizione.

### 5. Navigazione interna e routing unico

Tutte le surface applicative devono inserirsi in:

- layout comune
- sistema di routing unico
- pattern di navigazione condiviso

Ogni surface puo poi avere route interne proprie, ma senza rompere il frame applicativo comune.

### 6. Autorizzazione sempre governata dal backend

La sidebar ha funzione di:

- navigazione
- orientamento
- discoverability

Non definisce i permessi reali.

Regola:

- il backend valida sempre accesso a endpoint e dati
- il frontend nasconde cio che non e disponibile in sessione
- la presenza o assenza di una voce nella sidebar non sostituisce le guard backend

### 7. Compatibilita con surface future

Questo pattern e pensato per accogliere in modo coerente:

- `admin`
- future surface di dominio come `logistica`, `produzione`, `magazzino`

Il DL non definisce il design visivo della sidebar.
Definisce il modello di navigazione che le future surface devono rispettare.

## Esclusioni

Questo DL non definisce:

- design grafico dettagliato
- librerie frontend
- component library
- comportamento kiosk
- persistenza avanzata dello stato UI
- mapping semantico ruolo -> surface, che resta materia del backend e dei DL architetturali

## Consequences

### Positive

- migliore UX per utenti multi-ruolo
- separazione chiara tra login e navigazione
- crescita piu modulare del frontend
- contratto piu pulito tra backend e client

### Negative / Trade-off

- maggiore complessita iniziale del frontend
- necessita di rifattorizzare il flusso post-login esistente
- necessita di mantenere coerenti sidebar, routing e session contract

## Impatto sul progetto

Questo DL modifica:

- comportamento post-login del client browser
- struttura del layout applicativo
- pattern di navigazione globale delle surface

Deve guidare:

- i prossimi task UI/navigation
- le nuove surface applicative
- il refactor del chooser iniziale quando non sara piu necessario

## Notes

- Questo DL non sostituisce i DL architetturali su auth e surfaces; ne definisce la traduzione UI.
- Il passaggio e da "chooser iniziale obbligatorio" a "navigazione persistente multi-surface".
- `admin` e la prima surface concreta che puo beneficiare di questo pattern.

## References

- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/ARCH/DL-ARCH-V2-006.md`
