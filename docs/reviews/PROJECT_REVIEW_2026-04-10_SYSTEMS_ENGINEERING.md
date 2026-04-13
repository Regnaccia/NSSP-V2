# ODE V2 - Systems Engineering Review

## Date
2026-04-10

## Scope

Review completa del progetto `V2` con taglio `Systems Engineer`.

Focus:

- bootstrap e ripetibilita ambienti
- deployability e runtime assumptions
- readiness operativa
- health, diagnostics e observability
- gestione configurazione e segreti
- dipendenze esterne e modalita di failure
- backup, recovery e hygiene operativa

Obiettivo:

- capire quanto il sistema sia realmente eseguibile e governabile come runtime
- evidenziare gap operativi prima di pilot o produzione
- distinguere problemi di sola maturita da problemi che possono gia rallentare lo sviluppo

## Executive Summary

La V2 e forte sul piano del design applicativo e della documentazione di dominio, ma oggi resta un sistema principalmente:

- `developer-operated`
- `single-machine oriented`
- `manually bootstrapped`
- `lightly observable`

Come Systems Engineering baseline, il progetto e oggi adatto a sviluppo locale e demo controllate.
Non e ancora impostato come stack operativo robusto per:

- ambienti ripetibili oltre il laptop dello sviluppatore
- pilot con carico o continuita reale
- recovery disciplinato
- diagnosi rapida di fault runtime

## Findings

### 1. `health` e `ready` non misurano la salute reale del sistema

Gli endpoint di sistema restituiscono sempre `ok` e `ready` senza verificare database, migrazioni, configurazione minima o dipendenze runtime.

Riferimenti:

- [health.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/health.py:6)
- [health.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/health.py:11)

Rischio:

- un orchestratore o un operatore puo considerare sano un backend che non ha DB raggiungibile
- `ready` non protegge da startup incompleti, config errata o DB non migrato
- il segnale operativo e quindi poco utile per deploy, monitoraggio o smoke automation

Direzione di risoluzione:

- `health` minimale: processo vivo
- `ready`: check DB, config essenziale, eventualmente stato schema minimo
- distinguere chiaramente liveness da readiness

### 2. Il modello di deploy e ancora solo locale e incompleto

L'infrastruttura versionata contiene di fatto solo un compose per PostgreSQL locale.
Non emergono manifest o runbook equivalenti per backend, frontend, reverse proxy, secret injection o ambienti non locali.

Riferimenti:

- [infra/README.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/infra/README.md:1)
- [docker-compose.db.yml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/infra/docker/docker-compose.db.yml:12)
- [docker-compose.db.yml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/infra/docker/docker-compose.db.yml:16)

Rischio:

- ogni ambiente diverso dal laptop richiede decisioni operative non ancora codificate
- forte dipendenza da conoscenza implicita del maintainer
- assenza di un path chiaro `dev -> pilot -> production`

Direzione di risoluzione:

- fissare un target di deploy esplicito
- versionare la baseline del runtime completo, non solo il DB locale
- introdurre almeno un documento `deployment model` con prerequisiti e ownership operative

### 3. Il bootstrap documentato non e ancora affidabile come runbook eseguibile

La guida di bootstrap e dettagliata, ma non tutte le istruzioni risultano coerenti con il codice reale.
Un punto importante: `seed_initial.py` importa `engine`, ma `shared/db.py` espone `get_engine()` e non definisce `engine`.

Riferimenti:

- [seed_initial.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/scripts/seed_initial.py:27)
- [seed_initial.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/scripts/seed_initial.py:88)
- [db.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/db.py:17)
- [BACKEND_BOOTSTRAP_AND_VERIFY.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md:143)

Rischio:

- il runbook puo rompersi proprio nel punto piu critico del bootstrap
- la documentazione perde rapidamente affidabilita operativa
- i nuovi ambienti richiedono debug manuale invece di bootstrap ripetibile

Direzione di risoluzione:

- validare end-to-end il bootstrap documentato
- trattare le guide operative come artefatti testabili
- aggiungere un smoke bootstrap che copra almeno migrazione, seed e startup app

### 4. C'e drift tra runbook operativo e interfaccia API reale

La guida di bootstrap documenta endpoint che non corrispondono al router attuale.
Per esempio la guida cita `GET /api/produzioni`, mentre il router reale espone `/api/produzione/produzioni`.

Riferimenti:

- [BACKEND_BOOTSTRAP_AND_VERIFY.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md:199)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:42)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:175)

Rischio:

- smoke manuali e script di verifica possono colpire endpoint sbagliati
- gli operatori debugano problemi di routing che in realta sono problemi di documentazione
- il sistema diventa costoso da usare per chi non ha contesto storico

Direzione di risoluzione:

- riallineare immediatamente la guida al router reale
- preferire generazione o verifica automatica dei riferimenti API dove possibile

### 5. La gestione dei job operativi e sincrona, in-request e single-process

I refresh applicativi sono eseguiti dentro la request HTTP e la guardia di concorrenza e solo in-memory.
Questo e un modello accettabile in sviluppo, ma non scala bene a uso continuativo.

Riferimenti:

- [sync_runner.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py:13)
- [sync_runner.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py:46)
- [BACKEND_BOOTSTRAP_AND_VERIFY.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md:196)

Rischio:

- request lunghe e fragili per operazioni dipendenti da Easy e rebuild multipli
- collisioni o perdita di mutua esclusione appena si esce dal single-process
- assenza di retry, queueing, timeout policy e visibilita operativa sui job

Direzione di risoluzione:

- dichiarare il modello runtime attuale come `single-process only`
- prima del pilot valutare job async o almeno orchestration separata dalla request user-facing
- rendere persistente la guardia di concorrenza se il deployment evolve

### 6. L'osservabilita applicativa e molto limitata

Non emerge una baseline di logging applicativo, request correlation, metriche o tracing.
L'unica configurazione di logging evidente e quella di Alembic.

Riferimenti:

- [app/main.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/main.py:5)
- [alembic.ini](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/alembic.ini:6)
- [pyproject.toml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/pyproject.toml:10)

Rischio:

- errori runtime e degradazioni sono difficili da diagnosticare rapidamente
- manca visibilita su tempi delle request, esiti dei refresh, failure ricorrenti e dipendenze esterne
- il supporto operativo dipende da riprodurre il problema localmente

Direzione di risoluzione:

- introdurre logging applicativo coerente almeno per startup, auth e sync
- aggiungere identificatori di request/job
- preparare una baseline minima di metriche operative

### 7. La gestione configurazione e segreti non e ancora operational-grade

La root `env/` dichiara correttamente che non vanno committate credenziali reali, ma il progetto usa ancora `.env` locali e diversi script leggono il file direttamente invece di passare sempre dal layer di config condiviso.

Riferimenti:

- [env/README.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/env/README.md:3)
- [config.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/config.py:7)
- [sync_clienti.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/scripts/sync_clienti.py:40)

Rischio:

- comportamento diverso tra app server e script CLI
- duplicazione delle regole di risoluzione config
- maggiore probabilita di drift, segreti esposti o ambienti incoerenti

Direzione di risoluzione:

- centralizzare tutta la risoluzione config nel modulo shared
- evitare parsing manuale di `.env` negli script
- preparare un modello chiaro per secret injection per ambienti non locali

### 8. Il database di test e dichiarato, ma l'infrastruttura locale non lo prepara

La configurazione e la guida parlano di `DATABASE_URL_TEST` e di database test separato, ma il compose locale crea solo `nssp_v2`.

Riferimenti:

- [BACKEND_BOOTSTRAP_AND_VERIFY.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md:65)
- [docker-compose.db.yml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/infra/docker/docker-compose.db.yml:16)

Rischio:

- i test che presuppongono isolamento DB richiedono setup manuale implicito
- il bootstrap di test non e davvero self-contained
- aumenta la distanza tra flusso documentato e ambiente riproducibile

Direzione di risoluzione:

- creare esplicitamente `nssp_v2_test` nel bootstrap locale
- documentare chiaramente se il DB test va provisionato separatamente

### 9. Strategia di backup e recovery non visibile

L'infrastruttura locale monta un volume Docker persistente, ma non emergono procedure versionate di backup, restore, export dati o recovery drill.

Riferimenti:

- [docker-compose.db.yml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/infra/docker/docker-compose.db.yml:21)
- [scripts/README.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/scripts/README.md:3)

Rischio:

- una perdita del volume o un errore umano porta a recovery improvvisata
- nessuna garanzia sui tempi di ripristino
- knowledge operativa non ancora codificata

Direzione di risoluzione:

- definire almeno una procedura base di dump/restore per PostgreSQL
- chiarire cosa e ripristinabile da sync e cosa no
- distinguere dati ricostruibili da dati interni non ricostruibili

### 10. Assenza di startup governance applicativa

L'app FastAPI viene istanziata senza lifecycle hooks, startup checks o fail-fast su prerequisiti minimi.

Riferimenti:

- [app/main.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/main.py:5)

Rischio:

- l'app puo avviarsi in stato logicamente non pronto
- alcune failure emergono solo alla prima request reale
- l'operatore non ha un momento chiaro in cui il sistema valida i propri prerequisiti

Direzione di risoluzione:

- introdurre startup validation minima
- collegare readiness e startup checks
- fallire in modo esplicito quando il runtime e incoerente

## Classificazione Operativa

### Must Fix Now

- `Finding 1` - `health` e `ready` non misurano la salute reale del sistema
- `Finding 3` - bootstrap documentato non affidabile come runbook eseguibile
- `Finding 4` - drift tra runbook operativo e API reale
- `Finding 7` - gestione configurazione e segreti non ancora operational-grade

Motivo:

- impattano subito la fiducia operativa nel sistema
- rallentano bootstrap, debug e allineamento tra ambienti
- producono failure evitabili gia in fase di sviluppo condiviso

### Fix Before Pilot

- `Finding 2` - modello di deploy ancora solo locale e incompleto
- `Finding 5` - job operativi sincroni e single-process
- `Finding 6` - osservabilita applicativa molto limitata
- `Finding 8` - database di test dichiarato ma non provisionato
- `Finding 10` - assenza di startup governance applicativa

Motivo:

- questi punti iniziano a pesare seriamente appena il sistema viene usato in modo meno artigianale
- influenzano stabilita, diagnosi e operabilita del pilot

### Fix Before Production

- `Finding 9` - strategia di backup e recovery non visibile

Motivo:

- in produzione e un requisito non negoziabile
- in sviluppo puo restare implicito piu a lungo, ma non dovrebbe arrivare cosi a esercizio reale

## Verifica eseguita

Controlli effettuati:

- lettura della documentazione di bootstrap, infra e system overview
- ispezione di health endpoints, config, db bootstrap, seed e orchestration sync
- verifica della struttura `env/`, `infra/`, `scripts/`
- validazione del fatto che il runtime versionato copre soprattutto il DB locale

Limiti:

- l'ambiente corrente non aveva tutte le dipendenze Python installate
- non ho eseguito una prova completa di bootstrap end-to-end
- il worktree era gia sporco, quindi non ho trattato i cambi locali in corso come baseline stabile

## Cosa e gia buono dal punto di vista Systems

- layering chiaro e leggibile
- documentazione di bootstrap piu ricca della media
- dipendenza Easy mantenuta read-only
- esistenza di refresh semantici e freshness surface-oriented
- build frontend verificabile

## Suggested Follow-up

1. Creare un task di `operational bootstrap hardening` che chiuda seed, runbook e API drift.
2. Creare un task di `runtime readiness` per distinguere `health` e `ready`.
3. Fissare un decision log sul deployment target dei prossimi mesi.
4. Introdurre una baseline di logging applicativo e diagnosability.
5. Formalizzare backup/restore almeno per l'ambiente locale e il futuro pilot.

## References

- [SYSTEM_OVERVIEW.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/SYSTEM_OVERVIEW.md)
- [BACKEND_BOOTSTRAP_AND_VERIFY.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md)
- [PROJECT_REVIEW_2026-04-10_ARCHITECTURAL.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/PROJECT_REVIEW_2026-04-10_ARCHITECTURAL.md)
