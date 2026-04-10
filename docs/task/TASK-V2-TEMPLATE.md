# TASK-V2-XXX - Titolo task

## Status
Todo

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
YYYY-MM-DD

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`

## Goal

Descrivere in una frase l'obiettivo del task.

## Context

Spiegare il problema e il perche del task.

## Scope

- cosa va fatto
- quali file o moduli sono coinvolti
- quali artefatti devono risultare aggiornati

## Out of Scope

- cosa non va toccato
- cosa non deve essere ridefinito nel task

## Constraints

- vincoli architetturali
- vincoli tecnici
- limiti operativi o di rollout

## Refresh / Sync Behavior

Da compilare sempre quando il task introduce o modifica una vista UI che consuma:

- mirror `sync_*`
- fact canonici derivati
- freshness
- trigger di aggiornamento dati

Indicare esplicitamente uno di questi casi:

- `La vista non ha refresh on demand`
- `La vista riusa un refresh semantico backend gia esistente`
- `Il task introduce o modifica un refresh semantico backend dedicato`

Se la vista ha un pulsante `Aggiorna` o un comportamento equivalente, dichiarare:

- quale funzione semantica backend deve essere chiamata
- quali fact o slice vengono riallineati
- se al termine viene ricaricata solo la vista corrente o anche altro

Regola:

- non lasciare mai implicito il comportamento di refresh di una nuova vista UI
- evitare reload locali che sembrano refresh completi ma non riallineano le dipendenze
- se una vista dipende da fact derivati, il task deve dire esplicitamente come vengono aggiornati

## Acceptance Criteria

- criterio verificabile 1
- criterio verificabile 2
- criterio verificabile 3

## Deliverables

- file o moduli attesi
- test o verifiche attese
- documenti da aggiornare

## Verification Level

Dichiarare sempre esplicitamente uno di questi valori:

- `Mirata`
- `Full suite / milestone`

Regola:

- `Mirata` per fix o task intermedi, con test selettivi sul perimetro toccato
- `Full suite / milestone` per task che chiudono una milestone, consolidano un refactor o cambiano orchestration/contratti in modo ampio

## Environment Bootstrap

Comandi minimi per preparare l'ambiente di verifica del task in modo riproducibile.

Esempio per backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Se il task non introduce codice eseguibile, indicare esplicitamente: `N/A`.

## Verification Commands

Comandi da eseguire per verificare l'acceptance criteria del task.

Esempio:

```bash
pytest tests/unit/ -v
```

Specificare output atteso o exit code atteso.

Se `Verification Level = Mirata`, elencare solo test mirati coerenti col perimetro.

Se `Verification Level = Full suite / milestone`, includere esplicitamente la full suite richiesta.

## Implementation Notes

Note opzionali per chi esegue il task.

## Documentation Handoff

Di default la divisione dei compiti e questa:

- `Claude Code` aggiorna solo il file task corrente
- il riallineamento del resto della documentazione viene fatto successivamente da Codex o da un revisore documentale

Quindi, salvo istruzioni diverse nel task specifico:

- Claude deve aggiornare:
  - `Status`
  - `Completion Notes`
  - `Completed At`
  - `Completed By`
- Claude non deve perdere tempo a riallineare automaticamente:
  - `docs/task/README.md`
  - `docs/roadmap/TASK_LOG.md`
  - `docs/roadmap/STATUS.md`
  - `docs/SYSTEM_OVERVIEW.md`
  - guide e indici trasversali

Per rendere possibile questo handoff, le `Completion Notes` devono essere sufficientemente ricche da permettere il riallineamento senza dover riaprire tutto il codice.

---

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

### Summary

Cosa è stato fatto.

### Files Changed

- `path/to/file.py` — descrizione modifica

### Contracts / Flows Changed

Indicare esplicitamente:

- endpoint o contract API cambiati
- sequence / refresh chain cambiate
- fact o read model aggiunti o modificati
- comportamento utente visibile cambiato
- comportamento del refresh della vista, se presente

### Dependencies Introduced

- `pacchetto>=versione` — motivo

### Verification Provenance

Indicare per ogni verifica dichiarata:

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest tests/unit/ -v` | Claude Code (agente) | venv locale task | 2 passed |

Valori ammessi per "Eseguita da":
- `Claude Code (agente)` — eseguita dall'agente durante il task
- `Revisore esterno` — eseguita da persona in ambiente separato
- `Non eseguita` — con motivazione obbligatoria

### Assumptions

Assunzioni fatte durante l'implementazione.

### Known Limits

Limiti noti o aspetti non coperti.

### Documentation Impact

Indicare quali documenti trasversali andranno probabilmente riallineati dopo la chiusura del task, ad esempio:

- `docs/task/README.md`
- `docs/roadmap/TASK_LOG.md`
- `docs/roadmap/STATUS.md`
- `docs/SYSTEM_OVERVIEW.md`
- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`

### Follow-ups

- suggerimento per task successivo

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
