# DL-ARCH-V2-001 - Struttura repository V2 e confini espliciti tra sync, core e app

## Status
Approved

## Date
2026-04-02

## Context

Il charter V2 definisce una separazione forte tra `sync`, `core` e `app`, ma senza una
struttura repository coerente il rischio e ricadere nel pattern V1 dove la logica era
formalmente separata ma fisicamente concentrata sotto `app/services/`.

La V2 ha bisogno di:

- confini visibili anche a livello filesystem e import path
- contratti minimi tra layer prima di iniziare implementazione e bootstrap
- una base stabile per i successivi DL su facts, aggregate, rebuild e workflow applicativi

La V2 adotta una propria convenzione documentale esplicita:

- `DL-ARCH-V2-XXX` per le decisioni architetturali V2
- numerazione riavviata da `001`
- nessun `DL-OPS` attivo finché i concetti operativi non sono maturi

## Decision

La repository root coincide con la V2.

La documentazione generale V2 vive sotto:

- `docs/`

### 1. Struttura repository V2

```text
.
├── docs/
│   ├── archive/
│   ├── charter/
│   ├── decisions/
│   │   ├── ARCH/
│   │   └── OPS/
│   ├── guides/
│   ├── roadmap/
│   └── task/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── src/
│   │   └── nssp_v2/
│   │       ├── app/
│   │       ├── core/
│   │       ├── shared/
│   │       └── sync/
│   └── tests/
├── env/
├── frontend/
│   └── src/
├── infra/
│   └── docker/
└── scripts/
```

### 2. Confini dei layer backend

#### `sync`

Responsabilita:

- integrazione con EasyJob e altre sorgenti esterne
- connettori, estrazione, normalizzazione tecnica, load, change detection, run metadata
- scrittura di dati di sync e metadati di riallineamento

Vincoli:

- non contiene policy operative o decisioni di dominio
- non crea stati applicativi o workflow utente
- non dipende da FastAPI, router o componenti frontend

#### `core`

Responsabilita:

- costruzione di fatti canonici
- computed facts riusabili
- aggregate, stati operativi, policy, decision trace
- orchestrazione di rebuild completi o mirati

Vincoli:

- non conosce HTTP, router, Pydantic di trasporto o schermate frontend
- non contiene dettagli tecnici di EasyJob, ODBC o query della sorgente esterna
- e il centro semantico del sistema

#### `app`

Responsabilita:

- API HTTP
- autenticazione e dipendenze runtime
- workflow applicativi
- projection e contratti esposti al frontend o ad altri client

Vincoli:

- non reimplementa logica di dominio
- non decide policy operative
- non scrive direttamente dati di sync

#### `shared`

Responsabilita:

- configurazione
- accesso DB
- logging
- supporto tecnico comune

Vincoli:

- non e un layer di business
- non deve diventare contenitore generico di logica di dominio

### 3. Contratti espliciti tra layer

#### Contratto `sync -> core`

`sync` consegna al sistema:

- dati sorgente riallineati e persistiti
- change detection o run metadata utili al rebuild
- errori tecnici e stato del run

`core` non dipende da chiamate dirette al connettore della sorgente.  
Consuma solo input persistiti o contratti tecnici stabili.

#### Contratto `core -> app`

`core` espone:

- comandi e query di dominio
- DTO o strutture dati applicative stabili
- explainability e decision trace dove richiesto

`app` traduce questi output in API, pagine e workflow, senza ricalcolare le regole.

### 4. Regole di dipendenza

Dipendenze consentite:

- `app -> core`
- `app -> shared`
- `sync -> shared`
- `core -> shared`

Dipendenze non consentite:

- `core -> app`
- `core -> sync`
- `sync -> app`
- `frontend -> core` diretto

Il frontend comunica solo con l'`app layer` tramite contratti HTTP espliciti.

### 5. Struttura test

I test backend partono da:

- `tests/unit/`
- `tests/integration/`
- `tests/contracts/`
- `tests/sync/`

Regola:

- i test `unit` e `integration` del core devono poter validare il cuore del sistema senza EasyJob online
- i test `sync` verificano adattatori, normalizzazione e riallineamento senza contaminare i test core

## Notes

- Questa decisione blocca la struttura minima del repository V2 prima dell'implementazione.
- I successivi DL dovranno appoggiarsi a questi confini, non ridefinirli implicitamente.
- La struttura fisica e stata creata nella repository root, inclusa la documentazione generale in `docs/`.
- Il prossimo DL naturale riguarda bootstrap backend e contratti di persistenza del core.
