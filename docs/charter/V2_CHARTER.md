# V2_CHARTER.md

## Scopo del documento

Questo documento definisce il perimetro, i principi e il metodo di lavoro della V2 del sistema ODE OMR.

La V2 non nasce come semplice evoluzione incrementale della V1, ma come una rifondazione più chiara e disciplinata del sistema, costruita sulle lezioni apprese durante la V1 e orientata a:

- maggiore coerenza architetturale
- migliore implementabilità
- maggiore rigore nella separazione tra dato, calcolo e decisione
- preparazione a estensioni future in ambito produzione, logistica, magazzino e pianificazione

---

# 1. Obiettivi

## 1.1 Cosa deve fare il sistema

La V2 deve costruire una piattaforma operativa interna che:

1. acquisisce e riallinea i dati provenienti da EasyJob e da eventuali fonti native interne o esterne;
2. trasforma tali dati in una base canonica di fatti interni coerenti;
3. calcola informazioni derivate riusabili e stati operativi spiegabili;
4. supporta i reparti aziendali con viste, strumenti e decisioni operative coerenti;
5. consente rebuild completi o parziali in modo deterministico;
6. prepara il terreno per moduli più avanzati come:
   - pianificazione produzione
   - raccolta dati reparto
   - logiche di allocazione e priorità
   - simulazioni operative
   - automazioni future

## 1.2 Obiettivi operativi prioritari

La V2 deve essere progettata prima di tutto per supportare il flusso reale aziendale che va da:

- ordine cliente
- disponibilità articolo / fabbisogno
- produzione
- magazzino
- logistica
- spedizione

con particolare attenzione iniziale a:

- produzione
- schedulazione / rilascio lavoro
- coerenza tra domanda cliente, disponibilità e stato operativo reale

## 1.3 Cosa NON deve fare il sistema

La V2 non deve:

- diventare una copia passiva del gestionale;
- spostare logica di business nel layer di sync;
- duplicare logiche di dominio dentro UI o dashboard;
- dipendere da stati impliciti o accumulati in modo opaco;
- introdurre automazioni non spiegabili;
- ottimizzare prematuramente sacrificando chiarezza architetturale;
- cercare di coprire tutto il dominio aziendale in un unico rilascio iniziale.

La V2 deve restare focalizzata su una base corretta, rigenerabile ed estendibile.

---

# 2. Contesto

## 2.1 Contesto aziendale

Il sistema nasce per supportare il funzionamento operativo di OMR in un contesto manifatturiero/meccanico in cui il flusso informativo attraversa più reparti e oggi contiene ancora:

- passaggi manuali
- informazioni distribuite
- interpretazioni implicite
- decisioni locali non formalizzate

Il sistema deve ridurre questa frammentazione senza irrigidire l’operatività reale.

## 2.2 EasyJob come sorgente

EasyJob è una sorgente fondamentale del sistema, ma non coincide con la verità operativa completa.

EasyJob fornisce una parte importante dei dati di base, ma la V2 assume che il sistema interno debba poter integrare anche dati non presenti in Easy, come ad esempio:

- avanzamento produzione reale
- eventi macchina o reparto
- override operativi
- urgenze
- decisioni interne
- stati intermedi utili alla pianificazione

Di conseguenza il sistema è **core-centric**, non **Easy-centric**.

## 2.3 Reparti coinvolti

Il sistema è trasversale ai reparti:

- commerciale
- produzione
- magazzino
- logistica

ma il `core` non deve essere modellato per reparto.  
I reparti consumano proiezioni e viste, mentre la logica centrale resta unica e condivisa.

## 2.4 Flusso generale

Il flusso logico del sistema è:

**fonti esterne + fonti native → fatti canonici → calcoli derivati → stati operativi → proiezioni applicative**

Questo significa che il sistema distingue chiaramente tra:

- cosa sa
- cosa calcola
- cosa conclude
- cosa mostra

---

# 3. Principi guida

Questi principi sono considerati vincolanti.

## 3.1 Separazione forte dei layer

L’architettura è divisa in:

- `sync`
- `core`
- `app`

### `sync`
Acquisisce, normalizza e riallinea dati esterni.

### `core`
Costruisce fatti canonici, computed facts, stati operativi, policy e decision trace.

### `app`
Espone viste, azioni e workflow utente.

Regola:  
- `sync` non contiene logica operativa;
- `core` è il centro semantico del sistema;
- `app` non reimplementa la logica di dominio.

## 3.2 Core fact-centric

Il sistema non è centrato sulle schermate, né su un solo asse come ordine o articolo.

Il `core` è fact-centric:
- parte da fatti canonici
- costruisce computed facts
- costruisce stati operativi multi-asse
- espone projection per i diversi use case

## 3.3 Distinzione obbligatoria tra fatto, calcolo e stato

Nel modello V2 devono restare distinti:

- **Source Facts**: fatti canonici del dominio
- **Computed Facts**: valori derivati e riusabili
- **Operational States**: interpretazioni operative / decisionali
- **Projections**: viste per reparto o funzione

Questa distinzione non è opzionale.

## 3.4 Rigenerabilità e determinismo

Il `core` deve essere sempre ricostruibile a partire dagli input persistiti.

A parità di input, il risultato deve essere identico.

Non sono ammessi:
- stati nascosti non ricostruibili
- logiche dipendenti da esecuzioni precedenti non tracciate
- decisioni non spiegabili

## 3.5 Dependency chain esplicita

La propagazione dei cambiamenti deve essere esplicita e monitorabile.

Il `sync` espone cosa è cambiato.  
Il `core` decide cosa ricostruire.  
Le dipendenze non devono vivere come conoscenza implicita dispersa nel codice.

## 3.6 Aggregate root come unità di rebuild

La V2 deve ragionare per confini di coerenza reali.

Il rebuild non deve essere pensato solo “per tabella” o “per record”, ma per aggregate logici coerenti.

Questo principio è fondamentale per rendere implementabili:
- disponibilità
- domanda/offerta
- stato ordini
- shipping logic
- pianificazione futura

## 3.7 Policy esplicite e governate

Le policy devono essere oggetti espliciti del sistema.

Non devono essere:
- hardcodate in modo opaco nelle UI
- risolte “per caso”
- mischiate ai facts

Deve esistere:
- gerarchia di precedenza
- modello di conflict resolution
- tracciabilità degli override

## 3.8 Explainability nativa

Ogni stato operativo rilevante deve poter essere spiegato.

Il sistema non deve solo dire “cosa è vero”, ma anche “perché”.

La spiegazione deve essere strutturata e derivabile dal core, non affidata a testo manuale.

## 3.9 Modularità orientata all’estensione

La V2 deve essere progettata in modo da consentire in futuro l’aggiunta di moduli o servizi specializzati senza rompere il modello centrale.

In particolare, il sistema deve restare aperto a:
- motori di planning/scheduling
- servizi di simulazione
- raccolta dati shopfloor
- logiche avanzate di allocazione
- supporto decisionale e AI

---

# 4. Stack e strumenti

## 4.1 Principio generale

Lo stack deve essere scelto per:
- chiarezza
- robustezza
- facilità di sviluppo iterativo
- tracciabilità
- compatibilità con una crescita futura

La scelta tecnologica deve servire l’architettura, non guidarla.

## 4.2 Backend

### Python
Scelta come linguaggio principale per:
- rapidità di sviluppo
- leggibilità
- facilità nel modellare pipeline e logiche di dominio
- ottima compatibilità con elaborazioni dati, simulazioni e servizi futuri

### FastAPI
Scelta per:
- chiarezza contrattuale delle API
- buona integrazione con typing e validazione
- velocità di sviluppo backend
- compatibilità con servizi modulari futuri

## 4.3 Persistenza dati

### PostgreSQL
Scelto come database principale per:
- robustezza
- affidabilità
- supporto a modelli relazionali chiari
- buona base per crescita futura

### SQLAlchemy
Scelto come ORM / strato di accesso per:
- modellazione coerente delle entità
- controllo applicativo del mapping
- compatibilità con migrazioni e organizzazione modulare

### Alembic
Scelto per:
- versionamento schema
- tracciabilità delle evoluzioni del database
- gestione disciplinata dei cambi strutturali

## 4.4 Frontend

Il frontend V2 non è solo "React", ma un blocco tecnologico minimo coerente con quanto già validato in V1.

### React + TypeScript
Scelti per:
- modularità UI
- costruzione progressiva di dashboard e workflow
- facilità di sviluppo per sezioni/funzionalità
- buon fit per interfacce operative interne
- typing esplicito di contratti API, view model e stati UI

### Vite
Scelto per:
- avvio locale veloce
- build frontend semplice e leggibile
- buon supporto al workflow iterativo
- coerenza con il setup già usato in V1

### Tailwind CSS + UI primitives
Scelti per:
- costruzione rapida di interfacce interne coerenti
- riuso disciplinato di componenti UI
- riduzione di CSS sparso e ad hoc
- base solida per dashboard operative e workflow guidati

La V2 assume quindi come baseline frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- librerie UI/primitives coerenti con il setup già validato in V1

## 4.5 Ambiente e operatività

### Docker / Docker Compose
Scelti per:
- ambienti coerenti
- setup ripetibile
- semplificazione dell’avvio locale
- preparazione a deploy ordinati

### File `.env`
Usati per:
- separazione configurazione / codice
- gestione connessioni, credenziali e parametri runtime

## 4.6 Logging, contratti, documentazione

Sono parte integrante dello stack operativo:
- Decision Log architetturali
- documenti di implementazione
- contratti espliciti tra layer e servizi
- naming coerente
- struttura repository disciplinata

---

# 5. Metodo di sviluppo

## 5.1 Sviluppo guidato da charter + DL

La V2 viene sviluppata con questa gerarchia:

1. **Charter**
   - fissa scopo, principi e criteri di successo

2. **Decision Log**
   - fissano decisioni architetturali e logiche non banali

3. **Documenti di implementazione**
   - traducono i principi in piani concreti

4. **Codice**
   - implementa quanto deciso

Il codice non deve diventare il primo luogo in cui si scoprono le regole del sistema.

## 5.1.1 Convenzione dei Decision Log

I Decision Log vivono in:

- `docs/decisions/<TIPO>/`

Convenzioni minime:

- `DL-ARCH-V2-XXX`: decisioni architetturali V2, confini tra layer, contratti, scelte cross-cutting
- cartelle per tipo, ad esempio `ARCH/`, `OPS/`
- numerazione progressiva V2 a partire da `001`

Campi minimi di ogni DL:

- titolo
- status
- data
- context
- decision
- notes o consequences
- eventuali references ad altri documenti

Regole:

- una decisione ancora non validata resta in `docs/roadmap/POSSIBLE.md`, non diventa un DL approvato
- un DL può nascere `Proposed` e diventare poi `Approved`
- se un DL viene superato, il documento deve indicare chiaramente il successore
- per ora la V2 non usa la famiglia `DL-OPS`; i temi operativi restano in charter, roadmap e task finché non sono abbastanza chiari da essere fissati come decisione

## 5.2 Approccio incrementale ma disciplinato

Lo sviluppo deve procedere per milestone piccole ma semanticamente complete.

Ogni milestone deve:
- aggiungere un pezzo reale di sistema
- lasciare il modello più chiaro, non più confuso
- evitare scorciatoie che distruggono i principi del core

## 5.3 Prima la correttezza del modello, poi la copertura

La priorità non è “avere tutto”, ma “avere le fondamenta giuste”.

Meglio:
- meno funzionalità
- ma con confini chiari

che:
- molte feature
- con logica sparsa e difficilmente recuperabile

## 5.4 Documentazione viva

Ogni decisione importante deve lasciare traccia.

Devono essere documentati almeno:
- confini di dominio
- aggregate principali
- policy rilevanti
- contratti tra componenti
- ipotesi provvisorie
- punti ancora aperti

## 5.5 Best effort implementativo con revisione architetturale continua

La V2 va costruita anche per apprendimento empirico, ma senza perdere rigore.

Questo significa:
- implementare presto
- osservare dove il modello regge o si rompe
- correggere i documenti quando serve
- evitare però di cambiare direzione per dettagli locali non strutturali

## 5.6 Milestone suggerite

Ordine consigliato:

1. fondazioni architetturali V2, struttura repo e contratti tra `sync`, `core`, `app`
2. sync EasyJob affidabile e leggibile, con change detection e boundary chiaro verso il core
3. source facts canonici per ordini, righe ordine, articoli, stock, produzioni ed eventi rilevanti
4. computed facts essenziali per disponibilità articolo, copertura domanda e segnali di fabbisogno
5. aggregate principali del dominio, almeno su asse ordine e asse supply/demand articolo
6. primi stati operativi e workflow utili a produzione, in particolare disponibilità articolo, priorità e lancio produzione
7. prime projection applicative per produzione, logistica e magazzino senza duplicare logica nel frontend
8. policy governance, override e decision trace nei punti critici del flusso operativo
9. apertura a planning, scheduling e shopfloor data solo dopo stabilizzazione dei moduli core precedenti

Le milestone restano architetturali, ma devono sempre essere leggibili anche come avanzamento su moduli di dominio reali.  
Se un documento di implementazione parla di milestone, deve esplicitare quale problema operativo reale sblocca.

## 5.7 Punti aperti espliciti

I seguenti temi sono considerati aperti e non ancora stabilizzati nel charter:

- separazione planning layer / release layer
- make-or-buy come policy nativa del sistema
- routing e fasi di lavorazione come modello strutturato
- scheduler avanzato guidato da eventi o variazioni facts
- modalità di integrazione futura con shopfloor data e segnali reparto

Questi elementi vanno tracciati esplicitamente in `docs/roadmap/POSSIBLE.md` finché non vengono promossi a DL o a milestone implementativa confermata.

## 5.8 Strategia di test

La V2 deve definire e mantenere una strategia di test esplicita, distinta per layer:

- `core`: test unitari e deterministici sulle regole pure; test di integrazione su PostgreSQL reale per rebuild, aggregate e orchestrazione
- `sync`: test separati dal core; adapter e normalizzazione verificati con fixture o sorgenti controllate; integrazioni con sistemi esterni isolate e non mischiate ai test del core
- `app` / API: test di integrazione backend con `pytest`, API e database reale di test; dipendenze esterne e scheduler controllati o mockati
- frontend: test su utilità, hook e componenti critici; smoke test dei workflow principali quando il modulo UI diventa operativo

Il baseline tecnico atteso è:

- backend: `pytest`
- database di test: PostgreSQL reale dedicato
- frontend: test coerenti con stack React/TypeScript adottato

I test di sync verso sistemi esterni non devono diventare prerequisito per validare il core.  
I test del core devono poter girare in modo ripetibile senza dipendere da EasyJob online.

---

# 6. Criteri di successo

## 6.1 Successo architetturale

Una parte del sistema è riuscita se:

- il suo posto nell’architettura è chiaro;
- non introduce confusione tra sync, core e app;
- è rigenerabile;
- è spiegabile;
- ha dipendenze leggibili;
- non obbliga a logica duplicata nelle UI.

## 6.2 Successo operativo

Una funzione è riuscita se:

- aiuta davvero un reparto su un problema reale;
- riduce ambiguità operative;
- rende visibile uno stato prima implicito;
- migliora priorità, tempismo o coordinamento;
- non peggiora la flessibilità reale dell’azienda.

## 6.3 Successo tecnico

Una milestone è riuscita se:

- è testabile secondo la strategia definita in 5.8;
- è ricostruibile;
- è debuggabile;
- tollera full rebuild e rebuild mirati;
- non dipende da side effect opachi;
- lascia il codice più ordinato di prima.

## 6.4 Successo di prodotto interno

La V2 avrà successo se nel tempo riuscirà a diventare:

- riferimento operativo interno affidabile;
- estensione reale delle capacità di EasyJob;
- base comune per più reparti;
- piattaforma su cui innestare moduli futuri senza rifondare tutto.

## 6.5 Indicatori pratici

Segnali concreti che la direzione è corretta:

- una modifica in Easy o nei dati interni propaga effetti in modo comprensibile;
- un operatore può capire perché uno stato è stato assegnato;
- una logica può essere cambiata senza riscrivere metà sistema;
- nuove funzioni si appoggiano ai layer esistenti invece di aggirarli;
- produzione, magazzino e logistica possono leggere viste diverse senza avere tre verità diverse.

---

## Formula sintetica della V2

La V2 deve essere:

**più piccola della visione finale,  
ma già corretta nella struttura,  
rigenerabile nel comportamento,  
spiegabile nelle decisioni,  
ed estendibile senza rifondazione.**
