# DL-ARCH-V2-002 - Verifica riproducibile dei task e completion contract

## Status
Approved

## Date
2026-04-02

## Context

Il task `TASK-V2-001 - Bootstrap backend minimo V2` e stato il primo test reale
della pipeline:

`AI -> task -> codice -> architettura`

La verifica del risultato ha evidenziato che:

- la struttura del task e efficace
- il codice prodotto e coerente con i confini architetturali
- la pipeline e utilizzabile

Tuttavia sono emerse lacune importanti nella fase di verifica:

1. I test dichiarati non sono stati riproducibili in un ambiente pulito
   per assenza di istruzioni esplicite di setup.

2. Non esiste una procedura standard per:
   - installare le dipendenze
   - avviare il backend
   - eseguire i test

3. Il risultato del task e verificabile solo:
   - strutturalmente
   - ma non in modo deterministico a runtime

4. La completion del task non distingue chiaramente tra:
   - test effettivamente eseguiti
   - test non verificati

Questo crea un rischio sistemico:

Accumulo di task plausibilmente corretti ma non verificati in modo uniforme.

## Decision

La V2 introduce un `completion contract` esplicito e una `verifica riproducibile`
obbligatoria per tutti i task che producono codice o configurazione eseguibile.

### 1. Completion contract obbligatorio

Ogni task completato deve includere una sezione finale con:

- file creati o modificati
- dipendenze introdotte
- comandi eseguiti per verificare il risultato
- test eseguiti
- test non eseguiti, con motivazione
- assunzioni fatte
- limiti noti
- follow-up suggeriti

### 2. Verifica riproducibile obbligatoria

Ogni task che introduce codice o configurazione eseguibile deve permettere la verifica tramite:

- ambiente pulito, senza stato precedente implicito
- istruzioni esplicite di setup

Devono essere sempre forniti:

- comando per creare ambiente, `venv` o equivalente
- comando per installare dipendenze
- comando per avviare il servizio
- comando per eseguire i test

### 3. Separazione tra verifica strutturale e runtime

Ogni verifica deve distinguere chiaramente tra:

- verifica strutturale:
  - presenza file
  - rispetto architettura
- verifica runtime:
  - esecuzione codice
  - test automatici

Entrambe sono necessarie, ma non equivalenti.

### 4. Introduzione guide operative

Devono essere introdotte guide minime per bootstrap e verifica, ad esempio:

- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

Queste guide diventano parte del contratto operativo del progetto.

### 5. Aggiornamento template task

Il template `TASK-V2` deve essere aggiornato per includere:

- sezione `Verification`
- sezione `Expected Commands`
- sezione `Completion Output Required`

## Consequences

### Positive

- verifica consistente tra task diversi
- maggiore affidabilita del codice prodotto da AI
- riduzione ambiguita tra sembra corretto ed e verificato
- pipeline piu robusta e scalabile

### Negative / Trade-off

- aumento leggero della verbosita dei task
- maggiore disciplina richiesta nella scrittura e review
- tempi leggermente piu lunghi per completion iniziale

### Impatto sul progetto

Questo DL non modifica il dominio applicativo,
ma rafforza il metodo di sviluppo V2.

E considerato fondamentale prima di:

- introdurre facts canonici
- introdurre computed facts
- costruire aggregate e stati operativi

## Notes

- Questo DL deriva direttamente dal test `TASK-V2-001`
- I prossimi task devono gia rispettare questo contract
- La mancanza di verifica riproducibile e considerata un errore di processo, non di implementazione

## References

- `docs/task/TASK-V2-001-bootstrap-backend.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/test/TEST-V2-001-task-pipeline-validation.md`
