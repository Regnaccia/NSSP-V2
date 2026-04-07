# DL-ARCH-V2-007 - Sync model per entity

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 introduce l'integrazione con sistemi esterni, in particolare Easy,
come sorgente primaria dei dati operativi (clienti, destinazioni, ordini, articoli, ecc.).

E necessario definire un modello di sincronizzazione che sia:

- coerente con la regola di sola lettura verso Easy
- scalabile su piu entita
- testabile e osservabile
- separato dalle logiche di business del Core

Senza una struttura esplicita, il rischio e:

- creare un sync monolitico e poco controllabile
- mescolare logiche di acquisizione e logiche di business
- introdurre accoppiamenti forti con Easy

## Decision

La V2 adotta un modello di sincronizzazione per entita, basato su unita di sync backend dedicate.

### 1. Sync per entita

Ogni entita esterna sincronizzata e gestita da una unita di sync dedicata.

Esempi:

- sync clienti
- sync destinazioni
- sync ordini
- sync articoli

Ogni unita di sync e indipendente a livello logico e implementativo.

### 2. Easy come sorgente read-only

Le unita di sync leggono i dati da Easy esclusivamente in sola lettura.

Non e consentita alcuna scrittura verso Easy.

I dati vengono copiati o allineati nel sistema interno.

### 3. Responsabilita della sync

Ogni unita di sync ha responsabilita limitata a:

- acquisizione dati dalla sorgente esterna
- trasformazione tecnica minima (mapping campi, normalizzazione base)
- persistenza nel sistema interno

La sync NON deve:

- implementare logiche di business
- introdurre decisioni operative
- arricchire i dati con informazioni interne

### 4. Separazione Sync vs Core

Il sistema e diviso in due livelli distinti:

- Sync:
  - importa e allinea dati esterni
- Core:
  - costruisce relazioni
  - introduce dati interni
  - applica logiche di business

Regola:

> La sync trasferisce dati; il core costruisce significato operativo.

### 5. Idempotenza

Le unita di sync devono essere idempotenti.

Eseguire la stessa sync piu volte con lo stesso stato della sorgente
non deve produrre effetti inconsistenti o duplicazioni.

### 6. Trigger di esecuzione

Ogni unita di sync deve essere invocabile tramite:

- modalita on demand (manuale o via API)
- modalita schedulata

Compatibilita futura:

- trigger all'avvio sistema
- trigger da workflow applicativi
- rebuild mirato

### 7. Orchestrazione tra sync

Le unita di sync sono granulari per entita, ma possono avere dipendenze logiche.

Esempio:

- clienti prima di destinazioni
- anagrafiche prima di ordini

Il sistema deve poter orchestrare l'esecuzione delle sync
secondo dipendenze esplicite quando necessario.

### 8. Persistenza dati sincronizzati

I dati sincronizzati devono essere persistiti nel sistema interno
in strutture dedicate (mirror o staging interno).

Il Core deve lavorare su questi dati interni,
non accedere direttamente alla sorgente esterna.

## Esclusioni (out of scope)

Questo DL NON definisce:

- formato preciso delle tabelle di sync
- strategia completa di incremental sync
- gestione avanzata dei conflitti
- strumenti di scheduling specifici
- monitoraggio dettagliato e logging avanzato

Questi aspetti verranno definiti in DL o task successivi.

## Consequences

### Positive

- alta modularita del layer sync
- migliore testabilita e osservabilita
- chiara separazione tra acquisizione dati e logiche di business
- facilita di estensione a nuove entita

### Negative / Trade-off

- aumento numero di componenti (una sync per entita)
- necessita di gestire orchestrazione tra sync
- maggiore disciplina richiesta per mantenere separazione Sync/Core

## Impatto sul progetto

Questo DL introduce il modello di riferimento per:

- tutte le future integrazioni con Easy
- task di implementazione sync (clienti, destinazioni, ecc.)
- separazione architetturale tra Sync e Core

E prerequisito per:

- primo caso applicativo clienti/destinazioni
- definizione delle tabelle interne di sync

## Notes

- Questo DL e complementare alla policy di sola lettura verso Easy.
- Il modello privilegia semplicita e chiarezza rispetto a ottimizzazioni premature.
- I casi per singola entita non richiedono un nuovo `DL-ARCH` salvo che introducano un pattern architetturale nuovo rispetto al modello generale di sync.
- I casi specifici `clienti`, `destinazioni`, `articoli` devono vivere principalmente in:
  - documenti di mapping tecnico Easy
  - task di implementazione
  - eventuali DL aggiuntivi solo se emerge una regola nuova e riusabile oltre la singola entita

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-010-sync-clienti-reale.md`
- `docs/task/TASK-V2-011-sync-destinazioni.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
