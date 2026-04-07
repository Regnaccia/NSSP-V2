# DL-ARCH-V2-006 - Surface admin per access management

## Status
Approved

## Date
2026-04-07

## Context

Con i DL gia approvati, la V2 ha fissato:

- confini architetturali tra `sync`, `core`, `app`, `shared`
- contratto di verifica riproducibile dei task
- ruolo del database interno come persistence backbone
- modello di accesso utente, ruoli e canali client
- definizione stabile di `surface`

Dopo `TASK-V2-004`, il sistema puo autenticare un utente e instradarlo verso una o piu surfaces disponibili.

Resta pero un limite operativo importante:

- utenti e ruoli nascono ancora dal bootstrap tecnico
- il governo degli accessi non e ancora una capacita applicativa del sistema
- il progetto dipende ancora da seed e interventi tecnici per evolvere l'accesso

Prima di introdurre slices di dominio piu ricchi, la V2 ha bisogno di una prima surface reale che permetta di governare l'accesso in modo controllato.

Questa surface e:

- `admin`

Il DL serve a fissare in modo esplicito:

- scopo della surface `admin`
- confine tra ruolo `admin` e surface `admin`
- lifecycle minimo di utenti e ruoli
- regole minime di sicurezza
- cosa e esplicitamente fuori scope nel primo slice

## Decision

La V2 introduce `admin` come prima surface applicativa di governo del sistema, dedicata all'access management minimo.

Nel primo slice operativo, la surface `admin` copre solo:

- gestione utenti
- assegnazione ruoli
- stato attivo/inattivo
- visibilita delle surfaces risultanti dai ruoli

Non copre ancora permessi granulari, audit avanzato o configurazione completa del modello autorizzativo.

### 1. Admin e una surface, non un sinonimo di ruolo

`admin` come surface resta un concetto applicativo.

Il ruolo `admin` resta un concetto autorizzativo.

Nel primo slice V2 vale la regola operativa:

- il ruolo `admin` abilita la surface `admin`

Ma questa relazione non va interpretata come identita semantica permanente.

Regola:

- `role admin` abilita `surface admin`
- `role admin` non coincide ontologicamente con `surface admin`

### 2. Scopo della surface admin

La surface `admin` serve a governare il perimetro minimo di accesso al sistema.

Funzioni incluse nel primo slice:

- visualizzare gli utenti esistenti
- creare un nuovo utente
- attivare o disattivare un utente
- assegnare ruoli a un utente
- rimuovere ruoli da un utente
- visualizzare le surfaces risultanti dai ruoli assegnati

La surface `admin` non e pensata come pannello generico di sistema.

Nel primo slice non governa:

- parametri applicativi generali
- configurazione sync
- configurazione dominio
- cataloghi di business

### 3. Lifecycle minimo dell'utente

Il modello minimo di lifecycle gestito dalla surface `admin` e:

1. creazione utente
2. assegnazione ruoli
3. attivazione o disattivazione

Nel primo slice:

- l'utente e creato da un admin
- la password iniziale e impostata nel flusso amministrativo
- l'utente inattivo non puo autenticarsi

Non sono ancora parte del lifecycle:

- self-signup
- password reset self-service
- invito via email
- recupero password
- scadenza password

### 4. Catalogo ruoli e policy iniziale

Nel primo slice V2 il catalogo dei ruoli e controllato dal sistema.

Ruoli iniziali previsti:

- `admin`
- `produzione`
- `logistica`
- `magazzino`

La surface `admin` puo assegnare e rimuovere questi ruoli agli utenti, ma non ridefinisce il catalogo dei ruoli stesso.

Regola:

- la gestione del catalogo ruoli non entra nel primo slice admin

### 5. Surfaces derivate dal backend

Le surfaces disponibili a un utente sono derivate dal backend a partire dai ruoli assegnati e dalle policy applicative.

La surface `admin` puo mostrare le surfaces risultanti, ma non ne consente la modifica diretta.

Regola:

- la UI admin gestisce utenti e ruoli
- il backend continua a derivare `available_surfaces`
- la UI admin non modifica direttamente il mapping semantico `ruolo -> surfaces`

### 6. Regole minime di sicurezza

Il primo slice admin deve rispettare almeno queste regole:

- le password devono essere persistite con hash reale, non placeholder
- un utente inattivo non puo autenticarsi
- solo un utente con role `admin` puo usare la surface `admin`
- il backend resta fonte di verita per ruoli e surfaces disponibili

Protezione minima di consistenza:

- il sistema non deve permettere la rimozione dell'ultimo admin attivo senza una regola esplicita alternativa

Questa protezione e considerata obbligatoria gia nel primo slice, per evitare lock-out amministrativo.

### 7. Azioni non incluse nel primo slice

Per contenere la complessita, il primo slice `admin access management` non include:

- cancellazione fisica utenti
- audit trail avanzato
- cronologia modifiche
- permessi fine-grained per azione
- gruppi
- organizzazioni o tenancy
- gestione catalogo ruoli da UI
- gestione catalogo surfaces da UI
- password reset self-service

### 8. Confine backend/frontend

Backend:

- applica regole di autorizzazione admin
- valida operazioni su utenti e ruoli
- impedisce stati non ammessi
- espone dati coerenti per UI admin

Frontend:

- rende disponibile la surface `admin`
- mostra workflow chiari per utenti e ruoli
- non decide in autonomia policy critiche

### 9. Conseguenza sul piano dei task

Il task naturale successivo dopo questo DL e un task dedicato alla surface `admin` come primo modulo applicativo reale.

Ordine logico:

1. bootstrap backend
2. bootstrap DB interno
3. auth browser e routing iniziale
4. surface `admin` per access management

## Consequences

### Positive

- il sistema smette di dipendere dal seed come unico strumento di gestione accessi
- auth e ruoli diventano una capacita applicativa reale
- si crea una prima surface ad alto valore operativo ma a basso rischio di dominio
- la pipeline V2 puo essere testata su un workflow completo e governabile

### Negative / Trade-off

- introduce logica di governance prima delle prime superfici di dominio
- richiede alcune regole di sicurezza gia nel primo slice
- rinvia volutamente temi piu ricchi come audit e permessi granulari

### Impatto sul progetto

Questo DL non estende il dominio business della V2.

Rafforza pero il livello operativo del sistema e prepara il primo task applicativo reale dopo il bootstrap auth.

## Notes

- La surface `admin` e intenzionalmente stretta: gestisce accesso, non tutto il sistema.
- Il catalogo ruoli resta controllato dal sistema nel primo slice.
- Un DL successivo potra affrontare audit, permessi granulari o modelli di governance piu evoluti.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
