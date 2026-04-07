# TASK-V2-002 - Hardening verifica riproducibile backend

## Status
Todo

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-02

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/task/TASK-V2-001-bootstrap-backend.md`
- `docs/test/TEST-V2-001-task-pipeline-validation.md`

## Goal

Rendere riproducibile e verificabile in ambiente pulito il bootstrap backend introdotto da `TASK-V2-001`.

## Context

Il report `TEST-V2-001` ha dato esito `Pass con riserva`.

Il problema non e architetturale: il codice bootstrap prodotto risulta coerente con il task e con i confini `sync/core/app/shared`.

La lacuna emersa e invece metodologica e operativa:

- il task non fissava in modo esplicito il comando di bootstrap ambiente
- il repository non offre ancora una guida minima e diretta per installare le dipendenze backend
- la verifica dichiarata da Claude Code non e immediatamente riproducibile in un ambiente pulito senza ricostruire a mano i passaggi
- i completion notes non distinguono ancora in modo netto tra test eseguiti dall'agente e test riproducibili da chi legge il task

Questo task serve a implementare in modo operativo il contract fissato da
`DL-ARCH-V2-002` e a rinforzare la pipeline:

`AI -> task -> codice -> verifica -> architettura`

## Scope

- aggiornare il bootstrap documentale del backend con istruzioni minime, dirette e riproducibili
- esplicitare il comando di installazione dipendenze backend
- esplicitare il comando di avvio applicazione backend
- esplicitare il comando minimo di test per verificare il bootstrap
- aggiornare il template task V2 per includere una sezione dedicata alla verifica riproducibile
- aggiornare `TASK-V2-001` se necessario per renderlo retrospettivamente piu chiaro come artefatto
- lasciare traccia documentale chiara del fatto che questa attivita nasce dalle lacune emerse in `TEST-V2-001`

## Out of Scope

- nuove feature backend
- logica di dominio
- modelli SQLAlchemy di business
- sync EasyJob
- docker completo
- modifiche ai confini architetturali definiti in `DL-ARCH-V2-001`

## Constraints

- non introdurre nuova logica business
- mantenere la distinzione tra documentazione generale, task e report di test
- preferire soluzioni minime e operative, non framework documentali complessi

## Acceptance Criteria

- esiste una guida minima che permette a un collaboratore di installare il backend V2 e lanciare i test base senza inferenze
- il comando di verifica del bootstrap backend e documentato in modo esplicito
- il template task V2 include una sezione o campi che rendono obbligatoria la verifica riproducibile
- i completion notes distinguono chiaramente tra esecuzione effettuata dall'agente e verifica ripetibile da terzi
- la lacuna evidenziata in `TEST-V2-001` risulta chiusa o sensibilmente ridotta

## Deliverables

- aggiornamento di `backend/README.md` oppure guida dedicata sotto `docs/guides/`
- aggiornamento di `docs/task/TASK-V2-TEMPLATE.md`
- eventuale aggiornamento di `docs/task/TASK-V2-001-bootstrap-backend.md`
- summary finale con:
  - cosa e stato reso riproducibile
  - quali comandi devono essere usati
  - quali limiti restano aperti

## Implementation Notes

Direzione raccomandata:

- documentare il bootstrap backend con pochi comandi concreti
- aggiungere al template task campi tipo:
  - `Environment Bootstrap`
  - `Verification Commands`
  - `Verification Provenance`

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

- summary:
- files_changed:
- verification:
- followups:

## Completed At

YYYY-MM-DD HH:MM

## Completed By

Claude Code
