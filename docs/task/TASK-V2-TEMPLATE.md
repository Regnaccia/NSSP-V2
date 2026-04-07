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

## Acceptance Criteria

- criterio verificabile 1
- criterio verificabile 2
- criterio verificabile 3

## Deliverables

- file o moduli attesi
- test o verifiche attese
- documenti da aggiornare

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

## Implementation Notes

Note opzionali per chi esegue il task.

---

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

### Summary

Cosa è stato fatto.

### Files Changed

- `path/to/file.py` — descrizione modifica

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

### Follow-ups

- suggerimento per task successivo

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
