# DL-ARCH-V2-011 - Sync on demand backend-controlled

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 dispone gia di:

- sync unit per `clienti` e `destinazioni`
- run metadata e freshness anchor
- surface dati-dipendenti in arrivo

Prima di introdurre uno scheduler automatico, serve una modalita controllata per attivare la sync su richiesta.

Questa capacita e utile per:

- bootstrap operativo delle prime surface
- refresh manuale in caso di dati sospetti o stale
- debug e supporto operativo

Senza una regola esplicita, il rischio e:

- chiamare direttamente gli script dal frontend
- agganciare la UI a logiche di orchestrazione
- bypassare permessi, dipendenze e guard runtime

## Decision

La V2 introduce il modello di `sync on demand` governato dal backend.

Regola principale:

- la sync on demand puo essere richiesta dalla UI o da altri client
- ma viene sempre validata, orchestrata ed eseguita dal backend

La UI non invoca mai direttamente script, job runner o sorgenti Easy.

## 1. Trigger esterno, controllo interno

Il sistema distingue tra:

- richiesta di sync
- esecuzione effettiva della sync

La richiesta puo arrivare da:

- UI browser
- endpoint tecnico interno
- comando amministrativo controllato

L'esecuzione e sempre responsabilita del backend.

## 2. La UI non governa la sync

La UI puo solo:

- richiedere una sync on demand
- visualizzare stato e risultato

La UI non puo:

- decidere dipendenze runtime
- accedere direttamente a Easy
- eseguire script locali
- imporre bypass di controlli backend

Regola:

- frontend richiede
- backend decide

## 3. Modello minimo di API/backend contract

Il backend puo esporre trigger on demand per singola entita, ad esempio:

- `clienti`
- `destinazioni`

Oppure trigger di livello surface, se coerenti con le dipendenze del dominio.

Il contratto minimo deve permettere al chiamante di conoscere:

- se la richiesta e stata accettata
- quale job o run e stato avviato
- stato corrente o finale disponibile

Il DL non impone ancora il dettaglio HTTP definitivo.

## 4. Controlli obbligatori lato backend

Ogni richiesta di sync on demand deve essere sottoposta dal backend ad almeno questi controlli:

- autorizzazione del chiamante
- validita dell'entita richiesta
- rispetto delle dipendenze dichiarate
- prevenzione di esecuzioni concorrenti duplicate
- rispetto della policy read-only verso Easy

Esempio:

- `destinazioni` non deve essere lanciata ignorando la dipendenza da `clienti`

## 5. Modalita di esecuzione

Per il primo slice, il backend puo implementare la sync on demand in modo semplice e controllato.

Sono accettabili:

- esecuzione sincrona backend, se il tempo di risposta resta gestibile
- esecuzione asincrona o delegata, se gia disponibile nel perimetro tecnico

Regola:

- il modello di controllo viene deciso ora
- il modello tecnico di scheduling completo resta successivo

## 6. Relazione con freshness e bootstrap mode

La sync on demand e coerente con il modello runtime gia fissato.

In particolare:

- puo essere usata come trigger esplicito in bootstrap operativo
- puo essere usata come refresh manuale quando i dati risultano stale

Ma non sostituisce:

- la policy di freshness
- il futuro scheduler automatico

## 7. Osservabilita minima

Una sync on demand deve alimentare gli stessi metadati delle altre esecuzioni:

- `run_id`
- `status`
- `started_at`
- `finished_at`
- `rows_seen`
- `rows_written`
- `rows_deleted` se applicabile
- `error_message` se fallita

L'utente o client che richiede la sync deve poter leggere almeno un esito coerente con questi metadati.

## 8. Separazione da scheduler

Questo DL NON introduce ancora:

- scheduler periodico
- policy automatiche di refresh temporizzato
- orchestrazione avanzata multi-job

Regola:

- `sync on demand backend-controlled` e il passo intermedio tra script manuali e scheduler completo

## 9. Sicurezza e autorizzazione

La sync on demand e una capacita amministrativa o tecnica controllata.

Il backend deve poter limitare chi puo:

- richiedere una sync
- richiedere una sync per una certa entita
- leggere stato e risultato dell'esecuzione

Il DL non impone ancora il mapping finale `ruolo -> permesso di sync`, ma stabilisce che questa guardia vive nel backend.

## Esclusioni

Questo DL NON definisce:

- scheduler automatico
- tecnologia di job queue
- design finale degli endpoint HTTP
- surface UI del pulsante o workflow di refresh
- retry policy avanzate

## Consequences

### Positive

- evita accoppiamento diretto tra UI e layer `sync`
- crea un percorso operativo sicuro prima dello scheduler
- rende il refresh manuale compatibile con permessi, dipendenze e osservabilita

### Negative / Trade-off

- introduce un layer di controllo in piu rispetto al lancio diretto script
- richiede di definire guard backend e feedback di esecuzione
- non risolve ancora l'automazione periodica

## Impatto sul progetto

Questo DL diventa riferimento per:

- task backend di trigger `sync on demand`
- future azioni UI di refresh dati
- transizione dagli script manuali a un modello applicativo controllato

E precede logicamente:

- il task sul trigger backend di sync
- il futuro DL o task sullo scheduler automatico

## Notes

- Gli script manuali restano utili come supporto tecnico e debug.
- Il modello on demand non elimina la necessita futura di scheduling.
- La regola `Easy read-only` resta invariata e vincolante.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
