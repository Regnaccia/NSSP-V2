# TASK-V2-064 - Core effective planning policy articoli

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/task/TASK-V2-019-core-articoli.md`
- `docs/task/TASK-V2-063-model-planning-policy-defaults-e-overrides.md`

## Goal

Esporre nel Core `articoli` i valori effettivi delle planning policy, risolti con precedenza `override articolo` > `default famiglia`.

## Context

Dopo l'evoluzione del modello introdotta da `TASK-V2-063`, la V2 deve rendere disponibili ai moduli operativi i valori effettivi delle policy di planning.

I moduli futuri non devono leggere direttamente:

- il default di famiglia
- l'override articolo

e ricostruire ogni volta la regola di precedenza.

Serve invece che il Core `articoli` esponga almeno:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`

Questi valori effettivi diventeranno il contratto da consumare in:

- `criticita`
- `planning candidates`
- future policy di aggregazione

## Scope

### In Scope

- aggiornare il Core `articoli` per calcolare ed esporre:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
- applicare la regola:
  - override articolo se valorizzato
  - altrimenti default famiglia
- aggiornare read model / query / contract backend `articoli` dove rilevante
- test backend mirati sulla risoluzione dei valori effettivi

### Out of Scope

- UI di modifica degli override articolo
- consumo in `criticita`
- consumo in `planning candidates`
- nuove policy oltre alle due gia fissate
- refactor UI delle superfici esistenti

## Constraints

- i moduli operativi futuri devono poter consumare direttamente i valori effettivi
- la logica di risoluzione deve essere centralizzata nel Core, non duplicata nei consumer
- il task non deve ancora imporre l'uso dei nuovi campi nelle viste esistenti
- i naming devono restare coerenti con `DL-ARCH-V2-026`

## Acceptance Criteria

- il Core `articoli` espone `effective_considera_in_produzione`
- il Core `articoli` espone `effective_aggrega_codice_in_produzione`
- la precedenza `override articolo` > `default famiglia` e coperta da test
- i casi `override null` ereditano correttamente la famiglia

## Deliverables

- read model / query Core `articoli` aggiornati
- contratti backend aggiornati dove rilevante
- test backend mirati
- task aggiornato con completion notes ricche

## Verification Level

`Mirata`

Task di Core/read model, senza milestone UI.

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

Sono ammessi sottoinsiemi piu mirati se il task aggiunge test dedicati al Core `articoli`.

## Implementation Notes

Direzione raccomandata:

- mantenere la risoluzione delle policy vicino al Core `articoli`
- evitare helper duplicate nei moduli consumer
- esporre i valori effettivi nei read model gia esistenti se il contratto lo richiede, senza aprire ancora nuove viste

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Struttura dell'intervento

Tre file toccati nel Core `articoli`, nessun modulo consumer modificato:

```
core/articoli/
  read_models.py  — ArticoloItem e ArticoloDetail aggiornati
  queries.py      — resolve_planning_policy() + list_articoli() + get_articolo_detail()
```

### Helper centralizzato: `resolve_planning_policy`

```python
def resolve_planning_policy(
    override: bool | None,
    family_default: bool | None,
) -> bool | None:
    """
    effective = override if override is not None else family_default
    """
    if override is not None:
        return override
    return family_default
```

Centralizza la regola DL-ARCH-V2-026 §4 in un'unica funzione nel Core `articoli`.
I moduli consumer (`criticita`, `planning_candidates`, future policy) devono usare
questo helper senza ricostruire la precedenza localmente.

Semantica del valore restituito:
- `True`/`False`: valore effettivo risolto (da override o da famiglia)
- `None`: articolo senza famiglia e senza override — valore indefinito a livello di modello

### Read model aggiornati

**`ArticoloItem`** (lista sinistra UI) — due nuovi campi:

```python
effective_considera_in_produzione: bool | None
effective_aggrega_codice_in_produzione: bool | None
```

**`ArticoloDetail`** (dettaglio) — due nuovi campi con default None (backward-compatible
per serializzatori che non li includono):

```python
effective_considera_in_produzione: bool | None = None
effective_aggrega_codice_in_produzione: bool | None = None
```

### Query aggiornate

**`list_articoli`** — per ogni riga (art, config):

```python
family_considera = famiglia.considera_in_produzione if famiglia else None
family_aggrega   = famiglia.aggrega_codice_in_produzione if famiglia else None
override_considera = config.override_considera_in_produzione if config else None
override_aggrega   = config.override_aggrega_codice_in_produzione if config else None

effective_considera_in_produzione = resolve_planning_policy(override_considera, family_considera)
effective_aggrega_codice_in_produzione = resolve_planning_policy(override_aggrega, family_aggrega)
```

**`get_articolo_detail`** — logica identica, stessi quattro input.

### Comportamento con famiglia inattiva

`_load_famiglie_map` carica solo famiglie con `is_active=True`. Un articolo assegnato
a una famiglia inattiva risulta con `famiglia = None` → `family_default = None` →
`effective = None` (se non ha override). Questo è il comportamento corretto: una
famiglia inattiva non porta policy operative.

### Test mirati

`tests/core/test_core_effective_planning_policy.py` — 21 test in 3 classi:

- `TestResolvePlanningPolicy` (9): funzione pura — tutte le combinazioni
  (override True/False su default True/False, None eredita, None+None=None, override+None)
- `TestListArticoliEffectivePolicy` (6): effective policy in `ArticoloItem` —
  senza config, eredita famiglia, override prevale, policy indipendenti
- `TestGetArticoloDetailEffectivePolicy` (6): effective policy in `ArticoloDetail` —
  incluso il caso famiglia inattiva → None

### Verifica

```
python -m pytest tests/core tests/app -q
376 passed in 6.01s
```

Frontend non modificato — i nuovi campi sono additive nei contratti JSON (non breaking).

## Completed At

2026-04-10

## Completed By

Claude Code
