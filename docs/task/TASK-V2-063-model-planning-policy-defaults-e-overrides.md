# TASK-V2-063 - Model planning policy defaults e overrides

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`

## Goal

Evolvere il modello configurativo `famiglia + articolo` per supportare planning policy con default a livello famiglia e override puntuale a livello articolo.

## Context

Con `DL-ARCH-V2-026` la V2 ha fissato che le policy operative di planning devono seguire questa regola:

- default a livello `famiglia articolo`
- override puntuale a livello `articolo`
- precedenza: `override articolo` > `default famiglia`

La famiglia non deve essere usata per modellare eccezioni isolate.
Le eccezioni devono vivere sull'articolo.

Oggi il modello gia espone:

- famiglia articolo
- `considera_in_produzione` a livello famiglia

Serve ora preparare il modello per:

- reinterpretare `considera_in_produzione` come default operativo di planning
- aggiungere una seconda policy di default:
  - `aggrega_codice_in_produzione`
- introdurre override articolo nullable / tri-state per entrambe le policy

Questo task deve fermarsi al modello e alla persistenza.

## Scope

### In Scope

- evolvere il modello delle `famiglie articolo` per supportare:
  - `considera_in_produzione` come default di planning
  - `aggrega_codice_in_produzione` come default di aggregazione per codice
- introdurre nel modello/config articolo override nullable / tri-state per:
  - `considera_in_produzione`
  - `aggrega_codice_in_produzione`
- migration coerenti
- aggiornamento dei modelli backend rilevanti
- aggiornamento dei contratti backend di persistenza/configurazione dove necessario
- test backend mirati su persistenza, default e override

### Out of Scope

- calcolo dei valori effettivi nel Core `articoli`
- consumo nei moduli `criticita` o `planning candidates`
- UI di gestione override articolo
- redesign della UI famiglie
- modifica della logica di `TASK-V2-062`

## Constraints

- gli override articolo devono essere nullable / tri-state
- `null` significa eredita dal default di famiglia
- il task non deve hardcodare policy nei moduli di consumo
- il task deve preparare il modello, non anticipare ancora le projection effettive
- naming e semantica devono restare coerenti con `DL-ARCH-V2-026`

## Acceptance Criteria

- esiste il default di famiglia `aggrega_codice_in_produzione`
- il modello articolo supporta override nullable per:
  - `considera_in_produzione`
  - `aggrega_codice_in_produzione`
- il significato di `considera_in_produzione` come default di planning e riflesso nel modello/documentazione del task
- i test backend coprono:
  - default di famiglia
  - override articolo
  - ereditarieta via `null`

## Deliverables

- modelli backend aggiornati
- migration necessarie
- test backend mirati
- task aggiornato con completion notes ricche

## Verification Level

`Mirata`

Task di modello/persistenza, senza UI dedicata e senza milestone finale del modulo.

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

Sono ammessi comandi piu mirati se il task introduce test focalizzati sul modello `articoli/famiglie`.

## Implementation Notes

Direzione raccomandata:

- mantenere `considera_in_produzione` come nome stabile per il default di inclusione nel planning
- introdurre `aggrega_codice_in_produzione` con semantica esplicita e semplice
- per gli override articolo preferire campi nullable, non duplicare subito logiche di risoluzione
- nessuna UI di editing override in questo task

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Modello aggiornato

Due tabelle toccate, nessuna logica di consumo modificata.

#### `articolo_famiglie` — nuovo default planning policy

Aggiunto `aggrega_codice_in_produzione` (Boolean, NOT NULL, default False):

```python
# Prima:
considera_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

# Dopo:
considera_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
aggrega_codice_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

`considera_in_produzione` resta con lo stesso nome e default, ma viene riposizionato
architetturalmente come **default di planning policy** (non solo filtro locale di `criticita`).

Default False per `aggrega_codice_in_produzione`: comportamento conservativo — nessun
articolo diventa aggregabile per codice senza una scelta esplicita.

#### `core_articolo_config` — override nullable tri-state

Aggiunti due campi nullable:

```python
override_considera_in_produzione: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
override_aggrega_codice_in_produzione: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
```

Semantica tri-state (DL-ARCH-V2-026 §Override articolo):
- `None` → eredita dalla famiglia (comportamento invariato per tutte le righe esistenti)
- `True` → sovrascrive con True, indipendentemente dalla famiglia
- `False` → sovrascrive con False, indipendentemente dalla famiglia

#### Regola di risoluzione (effective policy)

```text
effective_value = override if override is not None else family_default
```

Questa regola è verificata nei test tramite `_resolve()` locale. La funzione Core
dedicata che la implementerà per i moduli di consumo è fuori scope di questo task.

### Migration

- `20260410_018_famiglia_aggrega_codice.py` — aggiunge `aggrega_codice_in_produzione`
  a `articolo_famiglie` con `server_default=0` (SQLite/PostgreSQL compatibile)
- `20260410_019_articolo_config_overrides.py` — aggiunge i due override nullable
  a `core_articolo_config` (NULL = eredita, nessun default a livello DB)

### Compatibilità con logiche esistenti

I moduli già in uso (`criticita`, `planning_candidates`) non sono stati modificati.
Entrambi leggono `ArticoloFamiglia.considera_in_produzione` direttamente — il campo
esiste ancora con lo stesso nome e semantica. Il riposizionamento architetturale
(da filtro locale a default planning policy) è documentativo, non strutturale.

### Test mirati

`tests/core/test_core_planning_policy.py` — 23 test in 3 classi:

- `TestFamigliaDefaultPolicy` (5): default False, policy esplicite, due famiglie distinte
- `TestArticoloConfigOverride` (8): null di default, True/False per entrambe le policy,
  aggiornamento e reset a null
- `TestEffectivePolicy` (10): tutte le combinazioni della regola di risoluzione
  (null→eredita, True prevale su False, False prevale su True, policy indipendenti,
  articolo senza famiglia)

### Verifica

```
python -m pytest tests/core tests/app -q
355 passed in 5.60s
```

## Completed At

2026-04-10

## Completed By

Claude Code
