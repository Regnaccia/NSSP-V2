# ODE V2 - Architectural Review

## Date
2026-04-10

## Scope

Review architetturale e di impostazione del progetto `V2` con focus su:

- configurazione runtime
- sicurezza applicativa
- autorizzazioni operative
- robustezza dei refresh e della concorrenza
- hygiene del repository e quality gates

Obiettivo:

- identificare problemi potenziali o impostazioni sbagliate del progetto
- distinguere i rischi strutturali dai normali task evolutivi
- fissare una baseline di hardening prima che il perimetro applicativo cresca ancora

## Sintesi

La V2 ha una direzione architetturale complessivamente buona:

- confini `sync / core / app / shared` leggibili
- documentazione unusually strong per lo stadio del progetto
- buona coerenza tra modello di dominio e surface operative
- frontend buildable e repository organizzato per stream reali

I rischi principali non stanno oggi nel disegno alto livello, ma nella distanza tra:

- architettura dichiarata
- enforcement effettivo nel codice
- posture di sicurezza
- automazione di verifica

## Findings

### 1. Presenza di credenziale reale nel repository e fallback JWT insicuro

Il file `backend/.env` contiene una connection string Easy con password in chiaro.
In parallelo il backend mantiene un default `jwt_secret_key = "change-me-in-production"` nel codice.

Riferimenti:

- [backend/.env](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/.env:14)
- [.gitignore](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/.gitignore:21)
- [config.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/config.py:17)

Rischio:

- esposizione di segreti in repository o backup locali
- token firmabili con chiave nota se l'ambiente non sovrascrive correttamente il secret
- falsa percezione di sicurezza per un progetto che ha gia auth e ruoli attivi

Direzione di risoluzione:

- rimuovere subito `backend/.env` dal versionamento e ruotare la credenziale Easy
- fallire il bootstrap se `JWT_SECRET_KEY` resta sul placeholder in ambienti non test
- separare nettamente sample config e config reale

### 2. Permessi troppo larghi sugli endpoint operativi

Molti endpoint che modificano stato interno o avviano refresh costosi richiedono solo autenticazione Bearer.
Non emerge una policy applicativa esplicita che distingua lettura, configurazione e operazioni amministrative.

Riferimenti:

- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:106)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:121)
- [produzione.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/produzione.py:199)
- [sync.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py:99)
- [sync.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py:162)

Rischio:

- qualsiasi utente autenticato puo alterare cataloghi interni, override o stato produzione
- qualsiasi utente autenticato puo lanciare refresh backend con impatto operativo
- il modello ruoli esiste ma non e ancora usato come boundary forte nelle mutazioni di dominio

Direzione di risoluzione:

- introdurre dependency di autorizzazione per capability operative, non solo `admin`
- distinguere esplicitamente `read`, `operate`, `configure`, `admin`
- riesaminare tutti gli endpoint `PATCH/POST` di surface sotto questa lente

### 3. Revoca ruoli e disattivazione utenti non effettive fino a scadenza token

Il backend emette un JWT che contiene i ruoli e poi, sulle request successive, si limita a verificare la firma.
Non c'e una rivalidazione contro il database dello stato utente o dei ruoli correnti.

Riferimenti:

- [auth.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/auth.py:51)
- [auth.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/auth.py:67)
- [deps/auth.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/deps/auth.py:21)
- [deps/admin.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/deps/admin.py:15)
- [config.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/config.py:19)

Rischio:

- un utente disattivato puo continuare a usare il sistema fino a scadenza del token
- un ruolo admin rimosso resta operativo per ore
- il controllo accessi e temporalmente incoerente rispetto alle azioni dell'admin

Direzione di risoluzione:

- usare il JWT come session envelope, ma rivalidare utente attivo e ruoli server-side
- in alternativa introdurre versioning/revocation dei token
- ridurre il TTL se il modello resta stateless

### 4. Concorrenza dei refresh adeguata solo a single-process

La guardia sulle sync usa lock in-memory ed e dichiarata adeguata solo a deployment single-process.
Questo e coerente con lo stato attuale, ma e un vincolo runtime forte e poco visibile.

Riferimenti:

- [sync_runner.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py:13)
- [sync_runner.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py:46)

Rischio:

- perdita della mutua esclusione con piu worker o piu istanze
- collisioni future con scheduler automatico, deployment robusti o job concorrenti
- assunzione infrastrutturale critica non enforcementata fuori dal codice

Direzione di risoluzione:

- introdurre lock/lease persistente su DB prima di passare a multi-worker
- rendere esplicito il vincolo single-process nella documentazione di deploy
- trattare questo punto come blocker prima di scheduler o background jobs

### 5. Drift tra configurazione esposta e comportamento reale

Il progetto espone alcune opzioni configurabili, ma in punti rilevanti il comportamento resta hardcoded.
Un caso concreto e la soglia di staleness: esiste in `Settings`, ma le API usano una costante locale.

Riferimenti:

- [config.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/config.py:26)
- [sync.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py:60)

Rischio:

- illusion of configurability
- comportamento runtime divergente da quanto il codice di configurazione suggerisce
- aumento del debito tecnico quando le policy di freshness cresceranno per surface o per entita

Direzione di risoluzione:

- consumare sempre `get_settings()` per policy runtime dichiarate configurabili
- evitare costanti duplicate per threshold o policy trasversali
- chiarire se la staleness deve essere globale, per surface o per entity

### 6. Bootstrap locale incompleto rispetto alla promessa di repository verificabile

Il frontend compila, ma il backend non e verificabile out-of-the-box nell'ambiente corrente senza installazione esplicita delle dipendenze di test.
Il repository non mostra inoltre quality gates automatici evidenti per CI.

Riferimenti:

- [backend/README.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/README.md:19)
- [pyproject.toml](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/pyproject.toml:21)
- [frontend/package.json](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/frontend/package.json:6)

Rischio:

- regressioni architetturali o di contratto non intercettate presto
- dipendenza eccessiva da verifica manuale e disciplina documentale
- repo apparentemente maturo ma poco enforced dal toolchain

Direzione di risoluzione:

- introdurre CI minima con `pytest`, build frontend e almeno un lint statico
- aggiungere script standardizzati per bootstrap e verify
- considerare quality gates come parte dell'architettura, non solo del processo

### 7. Persistenza del token browser in local storage

La sessione frontend usa `zustand/persist`, quindi il bearer token viene persistito nello storage del browser.
Per un tool interno puo essere una scelta accettabile in fase iniziale, ma e una decisione da governare.

Riferimenti:

- [authStore.ts](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/frontend/src/app/authStore.ts:35)

Rischio:

- esfiltrazione token in presenza di XSS o browser compromise
- superficie di attacco piu ampia rispetto a cookie `httpOnly`
- scelta di security implicita, non documentata come tradeoff

Direzione di risoluzione:

- documentare esplicitamente il tradeoff se si mantiene `localStorage`
- in alternativa migrare a cookie `httpOnly` o a una session strategy piu stretta
- trattare la superficie frontend come parte del modello di sicurezza, non solo come UI

### 8. Hygiene repository ancora incompleta

Nel repository sono presenti artefatti generati come `backend/src/nssp_v2.egg-info/`.
Non e un problema grave da solo, ma segnala che il repo non ha ancora una disciplina piena sugli output generati.

Riferimenti:

- [backend/src/nssp_v2.egg-info/PKG-INFO](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2.egg-info/PKG-INFO)

Rischio:

- rumore nei diff
- rischio di commit involontari di artefatti non sorgente
- minore chiarezza tra codice autorevole e output di packaging locale

Direzione di risoluzione:

- escludere gli artefatti generati dal controllo versione
- ripulire il repository e chiarire i path build/generated

## Classificazione Operativa

### Must Fix Now

Questi punti vanno affrontati subito anche in fase di sviluppo, perche rischiano di consolidare un modello sbagliato o esporre il progetto inutilmente.

- `Finding 1` - presenza di credenziale reale nel repository e fallback JWT insicuro
- `Finding 2` - permessi troppo larghi sugli endpoint operativi
- `Finding 3` - revoca ruoli e disattivazione utenti non effettive fino a scadenza token

Razionale:

- toccano direttamente security posture e controllo accessi
- se lasciati sedimentare, diventano molto piu costosi da correggere
- impattano il modello architetturale, non solo l'hardening finale

### Fix Before Pilot

Questi punti non bloccano la prosecuzione immediata dello sviluppo, ma vanno chiusi prima di un pilot con utenti piu reali, uso continuativo o maggiore pressione operativa.

- `Finding 4` - concorrenza dei refresh adeguata solo a single-process
- `Finding 5` - drift tra configurazione esposta e comportamento reale
- `Finding 6` - bootstrap locale incompleto e quality gates deboli

Razionale:

- influenzano affidabilita, coerenza runtime e verificabilita del sistema
- diventano rischi concreti appena il progetto esce dal perimetro di sviluppo controllato
- sono fondamentali per evitare regressioni e collisioni operative durante un pilot

### Fix Before Production

Questi punti possono attendere piu degli altri se il sistema resta interno e in contesto controllato, ma non dovrebbero arrivare invariati a una messa in produzione vera.

- `Finding 7` - persistenza del token browser in local storage
- `Finding 8` - hygiene repository ancora incompleta

Razionale:

- il rischio esiste, ma e piu dipendente dal contesto di esposizione reale
- non altera subito il disegno architetturale centrale
- resta comunque opportuno chiuderli prima di un uso stabile o auditabile

## Verifica eseguita

Controlli svolti durante la review:

- lettura della struttura repository e della documentazione attiva
- ispezione dei file di configurazione backend e frontend
- verifica dei boundary auth / admin / sync
- build frontend eseguita con successo tramite `npm run build`

Limiti della verifica:

- i test backend non sono stati eseguiti nell'ambiente corrente per assenza del modulo `pytest`
- il worktree era gia sporco, quindi la review non valuta semanticamente tutte le modifiche locali in corso

## Cosa non emerge come problema strutturale

Non emergono oggi problemi gravi sui confini concettuali principali:

- separazione `sync / core / app / shared`
- scelta di mantenere Easy `read-only`
- direzione dei primi computed fact canonici
- allineamento generale tra modello documentato e navigazione per surface

La direzione architetturale resta valida.
Il gap vero e tra un buon disegno e un enforcement operativo ancora incompleto.

## Suggested Follow-up

1. Aprire un task tecnico di `security hardening` per segreti, JWT e session model.
2. Aprire un task tecnico di `authorization hardening` sugli endpoint `PATCH/POST` e sui trigger di sync.
3. Fissare un decision log sul modello target di deploy: `single-process esplicito` oppure `preparazione multi-worker`.
4. Introdurre una baseline CI minima con build frontend e test backend.
5. Ripulire gli artefatti generati dal repository e formalizzare il bootstrap verificabile.

## References

- [README.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/README.md)
- [AI_HANDOFF_CURRENT_STATE.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/AI_HANDOFF_CURRENT_STATE.md)
- [STATUS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/roadmap/STATUS.md)
- [PROJECT_REVIEW_2026-04-08.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/PROJECT_REVIEW_2026-04-08.md)
