# TASK-V2-068 - Hardening Planning Candidates: escludere produzioni completate

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-033-forza-completata-produzioni.md`
- `docs/task/TASK-V2-062-core-planning-candidates-v1.md`

## Goal

Correggere il calcolo di `incoming_supply_qty` in `Planning Candidates` V1 escludendo le produzioni gia `completate`, anche quando il completamento deriva da override interno.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-030`
- `TASK-V2-033`
- `TASK-V2-062`

## Context

`Planning Candidates` V1 usa `incoming_supply_qty` come supply gia in corso per calcolare:

- `future_availability_qty = availability_qty + incoming_supply_qty`

Nel primo slice di `TASK-V2-062`, la supply in arrivo viene aggregata dalle produzioni attive in modo semplice e time-agnostic.

Nelle completion notes del task e documentato un limite noto:

- le produzioni marcate `completata` tramite override `forza_completata` non vengono escluse dal calcolo planning

Questo puo sovrastimare `future_availability_qty` e nascondere candidate reali.

Per il planning operativo V1, una produzione `completata` non deve piu essere considerata supply in corso, indipendentemente dal fatto che il completamento derivi:

- dallo stato Core computato
- oppure da override interno

## Scope

### In Scope

- aggiornare il calcolo `incoming_supply_qty` di `Planning Candidates` V1
- escludere dal contributo supply tutte le produzioni che nel Core risultano `completate`
- includere esplicitamente anche il caso `forza_completata`
- aggiornare i test mirati del modulo planning
- aggiornare le completion notes del task o il nuovo task con il comportamento effettivo

### Out of Scope

- modifica della UI `Planning Candidates`
- modifica della formula generale di `future_availability_qty`
- introduzione di orizzonte temporale
- scoring
- nuove policy di aggregazione

## Constraints

- la logica deve usare la nozione effettiva di produzione `completata`, non solo il mirror raw `sync_produzioni_attive`
- il task non deve indebolire la semplicità V1 del modulo
- il comportamento deve restare time-agnostic: si corregge solo il perimetro della supply in corso

## Refresh / Sync Behavior

La vista UI non e in scope in questo task.

Quindi:

- `La vista non ha refresh on demand`
- il task modifica solo la logica Core di `Planning Candidates`

## Acceptance Criteria

- `incoming_supply_qty` esclude le produzioni `completate`
- una produzione marcata `completata` via `forza_completata` non contribuisce alla supply in arrivo
- `future_availability_qty` riflette correttamente questa esclusione
- i test coprono il caso:
  - produzione attiva raw ma completata via override

## Deliverables

- hardening della query/logica Core `Planning Candidates`
- test backend mirati
- task aggiornato con completion notes ricche

## Verification Level

`Mirata`

Task di hardening localizzato sul Core planning.

## Environment Bootstrap

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

Sono ammessi sottoinsiemi piu mirati se il task aggiunge test dedicati a `planning_candidates`.

## Implementation Notes

Direzione raccomandata:

- preferire il Core `produzioni` o una nozione equivalente di stato effettivo rispetto al solo mirror raw
- non reintrodurre nella query planning logiche duplicate o incoerenti con il Core `produzioni`
- documentare esplicitamente il superamento del limite noto lasciato in `TASK-V2-062`

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Problema corretto

`_compute_incoming_supply` in `core/planning_candidates/queries.py` leggeva da `sync_produzioni_attive` senza consultare `core_produzione_override`. Una produzione con `forza_completata=True` e `quantita_prodotta < quantita_ordinata` veniva contata come supply in arrivo, gonfiando `future_availability_qty` e potenzialmente nascondendo candidate reali.

### Fix applicato

**`core/planning_candidates/queries.py`**:
- Aggiunto import `CoreProduzioneOverride` e `and_`
- `_compute_incoming_supply` esegue ora un `OUTERJOIN` su `core_produzione_override` (bucket='active')
- Filtro aggiunto: `forza_completata = False OR forza_completata IS NULL`
  - produzioni senza override: left join restituisce NULL → incluse (comportamento invariato)
  - produzioni con `forza_completata=False`: incluse normalmente
  - produzioni con `forza_completata=True`: escluse dalla supply
- Le produzioni naturalmente completate (`prodotta >= ordinata`) continuano a contribuire 0 tramite clamp Python (`max(remaining, 0)`)
- Docstring aggiornato: rimossa nota "V1 tradeoff: forza_completata non considerato"; documentato superamento del limite

### Test aggiunti

Nuova classe `TestForzaCompletata` in `tests/core/test_core_planning_candidates.py` (5 test):
- `test_forza_completata_esclusa_da_supply` — caso base: produzione forzata non contribuisce
- `test_forza_completata_false_inclusa_nella_supply` — override False: produzione inclusa
- `test_senza_override_inclusa_nella_supply` — nessun record override: produzione inclusa (left join NULL)
- `test_mix_forza_completata_e_attiva` — mix di produzioni: solo quelle non-forzate contribuiscono
- `test_forza_completata_scopre_candidate_nascosto` — scenario critico: candidato che prima veniva mascherato dalla supply forzata, ora visibile

### Verifica

- `pytest tests/core/test_core_planning_candidates.py` → 39 passed
- `pytest tests/core tests/app -q` → 381 passed

## Completed At

2026-04-10

## Completed By

Claude Code
