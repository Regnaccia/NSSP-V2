# DL-ARCH-V2-008 - Sync execution model and freshness policy

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

`DL-ARCH-V2-007` ha definito il modello strutturale della sincronizzazione per entita,
basato su unita di sync indipendenti e sulla separazione tra Sync e Core.

E ora necessario definire il modello di esecuzione runtime della sincronizzazione,
inclusi:

- scheduling
- trigger di esecuzione
- gestione dei rebuild
- policy di freschezza dei dati
- comportamento all'accesso delle surface
- dipendenze tra entita

Senza un modello esplicito, il rischio e:

- esecuzioni incoerenti o ridondanti
- refresh gestiti in modo ad hoc nelle UI
- accoppiamento tra layer UI e layer Sync
- perdita di controllo sulla qualita e freschezza dei dati

## Decision

La V2 adotta un modello di esecuzione della sincronizzazione basato su:

- job di sync per entita
- scheduling configurabile
- policy di freschezza dichiarative
- orchestrazione centralizzata
- gestione esplicita delle dipendenze

### 1. Sync job per entita

Ogni unita di sync definita in `DL-ARCH-V2-007` e esposta come un job eseguibile.

Ogni job e identificato da:

- `entity_code` (es. clienti, destinazioni, ordini)

Il job e:

- idempotente
- ri-eseguibile in sicurezza
- indipendente a livello logico

### 2. Registry dei job di sync

Il sistema mantiene una configurazione interna dei job di sync.

Configurazione minima per ogni entita:

- `entity_code`
- `is_enabled`
- `interval_minutes`
- `allow_on_demand`
- `allow_startup`
- `allow_daily_rebuild`
- `priority`
- `staleness_threshold_minutes`

Stato runtime minimo:

- `last_run_at`
- `last_success_at`
- `last_status`
- `last_error`

Questa configurazione rappresenta la policy di esecuzione.

Nota:

Il registry dei job comprende sia configurazione (policy di esecuzione)
sia stato runtime (telemetria operativa).

La loro persistenza puo essere:

- unificata
- oppure separata (config vs stato)

Questa distinzione e logica e non vincola l'implementazione tecnica.

### 3. Modalita di esecuzione

Ogni job di sync puo essere attivato tramite:

#### 3.1 On demand

- invocazione manuale via API o comando interno
- utilizzata da:
  - operatori
  - workflow applicativi
  - debug

#### 3.2 Schedulata

- esecuzione automatica secondo `interval_minutes`
- gestita da scheduler interno

#### 3.3 All'avvio

- esecuzione opzionale all'avvio del sistema
- controllata da configurazione (`allow_startup`)

#### 3.4 Full rebuild giornaliero

- esecuzione globale o per entita a orario fisso
- finalita:
  - riallineamento completo
  - correzione derive

#### 3.5 Full sync manuale

- attivabile solo tramite backend controllato
- puo essere:
  - globale
  - per singola entita

### 4. Rebuild policy

Il sistema supporta una modalita di full rebuild, che:

- riesegue la sincronizzazione completa delle entita
- riallinea il sistema interno alla sorgente Easy

Tipologie:

- rebuild all'avvio
- rebuild giornaliero
- rebuild manuale

Il rebuild e piu costoso della sync ordinaria e deve essere usato con controllo.

### 4.b Terminologia: Sync rebuild vs Core rebuild

In V2 il termine "rebuild" e utilizzato in due contesti distinti e non deve essere ambiguo.

#### Sync rebuild

- riguarda il layer Sync
- consiste nella riesecuzione completa della sincronizzazione delle entita
- obiettivo: riallineare il sistema interno alla sorgente esterna (Easy)

#### Core rebuild

- riguarda il layer Core
- consiste nella ricostruzione di relazioni, stati e dati derivati
  a partire dai dati gia sincronizzati internamente
- obiettivo: ripristinare coerenza del modello operativo

Regola:

> Sync rebuild e Core rebuild sono concetti distinti e non devono essere confusi.

Le operazioni di sync non devono eseguire logiche di core rebuild.

### 5. Freshness policy

Ogni entita sincronizzata ha una soglia di freschezza:

- `staleness_threshold_minutes`

Questa definisce quando i dati sono considerati stale.

Regola:

- se `now - last_success_at > threshold`, i dati sono stale

Default:

- il sistema puo definire una soglia di freschezza globale di default
- le singole entita possono override tale valore

Questo garantisce coerenza tra le diverse unita di sync.

### 6. Accesso alle surface e refresh

Ogni surface applicativa dichiara esplicitamente le entita richieste.

Esempio:

- surface logistica clienti/destinazioni:
  - richiede: clienti, destinazioni

Quando una surface viene aperta:

1. il sistema verifica la freschezza delle entita richieste
2. comportamento standard:
   - se i dati sono freschi, render immediato
   - se i dati sono stale, avvio sync in background

Regola di default:

> Il refresh non deve essere bloccante per la UI.

Eccezioni future potranno introdurre surface o workflow con refresh bloccante.

### 6.b Bootstrap mode (no local snapshot yet)

Caso speciale: primo accesso a una surface quando non esiste ancora alcuno snapshot locale
per una o piu entita richieste.

Condizione:

- non esiste alcun dato sincronizzato persistito per almeno una delle entita richieste
- oppure non esiste alcuna esecuzione di sync completata con successo

In questo caso il sistema entra in modalita bootstrap:

1. viene attivata la sync necessaria per le entita richieste
2. la UI entra in stato bloccante controllato (loading esplicito)
3. la surface non mostra dati parziali o vuoti non intenzionali

Uscita dalla modalita bootstrap:

- al completamento con successo della prima sync, render dei dati
- in caso di errore, stato errore esplicito

Regola:

> La modalita bootstrap e l'unico caso in cui il refresh puo essere bloccante per la UI.

Questo comportamento e distinto dal caso stale data, che resta non bloccante.

### 7. Refresh non bloccante

Quando i dati risultano stale:

- la UI mostra i dati disponibili
- viene avviata una sync in background
- la UI puo:
  - notificare l'utente
  - aggiornarsi al completamento

Questo evita:

- dipendenza diretta da Easy
- degrado UX

### 8. Dependency model

Le dipendenze tra entita sono esplicite.

#### 8.1 Dependency di sync

Definisce l'ordine di esecuzione tra job:

- destinazioni dipendono da clienti
- ordini dipendono da clienti e articoli

Il sistema deve rispettare queste dipendenze durante l'orchestrazione.

#### 8.2 Dependency di surface

Ogni surface dichiara:

- quali entita sono necessarie

Questo consente di:

- verificare la freschezza
- attivare refresh mirati

Regola:

Le dependency di sync e le dependency di surface sono concetti distinti
e devono essere modellate separatamente.

- le sync dependency governano l'ordine di esecuzione tecnica
- le surface dependency governano la disponibilita dei dati per la UI

### 9. Orchestrazione

Un componente di orchestrazione gestisce:

- esecuzione dei job
- rispetto delle dipendenze
- prevenzione di esecuzioni concorrenti duplicate
- priorita dei job
- gestione degli errori

Le chiamate dirette ai job di sync dalla UI devono essere evitate.

### 10. Separazione UI / Sync

La UI:

- non accede direttamente a Easy
- non implementa logica di sync
- richiede dati al backend

Il backend:

- decide se attivare sync
- restituisce dati disponibili

## Esclusioni (out of scope)

Questo DL NON definisce:

- implementazione tecnica dello scheduler
- tecnologia di orchestrazione
- dettagli di locking distribuito
- retry policy avanzate
- monitoring e alerting avanzato

## Consequences

### Positive

- controllo esplicito del comportamento runtime della sync
- maggiore robustezza e prevedibilita
- migliore UX grazie a refresh non bloccante
- base solida per scalabilita futura

### Negative / Trade-off

- maggiore complessita iniziale
- necessita di orchestrazione esplicita
- gestione configurazioni piu articolata

## Impatto sul progetto

Questo DL definisce:

- come e quando vengono eseguite le sync
- come le surface interagiscono con il layer dati
- la base per i primi task di sync (clienti, destinazioni)

E prerequisito per:

- primo caso applicativo clienti/destinazioni
- definizione delle surface dati dipendenti da freshness

## Notes

- Questo DL completa `DL-ARCH-V2-007` introducendo il modello runtime.
- Il sistema privilegia consistenza e controllo rispetto ad aggiornamento immediato.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
