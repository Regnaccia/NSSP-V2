# TASK-V2-130 - UI admin proposal logic two-column governance

## Status
Completed

## Date
2026-04-16

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-033.md`

## Goal

Rifinire la pagina admin delle logiche proposal con un layout a `2 colonne` e con primitive di governance piu esplicite:

- lista logiche a sinistra
- dettaglio logica a destra
- flag `enabled`
- azione `delete`

## Context

La pagina admin attuale delle logiche proposal e ancora modellata come form singolo con select + JSON params.

Per le logiche proposal sta emergendo un bisogno di governance piu chiaro:

- leggere subito le logiche disponibili
- capire quale logica e selezionata
- vedere una descrizione human-friendly della logica
- governare se una logica e attiva o eliminabile

Inoltre, la selezione articolo-specifica deve essere coerente con lo stato di attivazione:

- una logica puo essere assegnata agli articoli solo se `enabled = true`

## Scope

- ridisegnare la page admin proposal logic nello schema UI a `2 colonne`
- colonna sinistra:
  - elenco logiche disponibili
  - evidenza della logica selezionata
- colonna destra:
  - key tecnica
  - label umana
  - descrizione human-friendly
  - parametri globali JSON
  - stato `enabled`
  - azione `delete`
- fissare il contratto UI che impedisce l'assegnazione agli articoli di logiche non abilitate

## Out of Scope

- implementazione backend completa del lifecycle CRUD delle logiche
- redesign della UI `articoli`
- cambio del modello concettuale delle proposal logic nel rebase

## Constraints

Regole minime:

- la pagina adotta il pattern UI a `2 colonne`
- una logica `disabled` resta leggibile in admin ma non puo essere assegnata agli articoli
- l'azione `delete` deve essere pensata come governance esplicita, non come rimozione implicita dal catalogo senza guardrail
- il task puo introdurre inizialmente solo il comportamento UI/contract se il backend CRUD completo non e ancora pronto

Vincolo di coerenza:

- la surface `articoli` deve consumare solo logiche `enabled = true`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Possibile
- `Introduce configurazione interna governata da admin?` Si
- `Introduce configurazione che deve essere visibile in articoli?` Si
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 01 - Entita governata in admin, consumata nelle surface operative`
- `Pattern 04 - Core read model prima della UI`
- `Pattern 06 - Multi-colonna standard per catalogo + dettaglio`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La pagina admin proposal logic resta una configurazione interna.

## Acceptance Criteria

- la pagina admin proposal logic usa il pattern a `2 colonne`
- l'elenco logiche e separato dal dettaglio della logica selezionata
- ogni logica ha almeno:
  - `key`
  - `label`
  - `description`
  - `enabled`
- il contratto impedisce l'assegnazione agli articoli di logiche `enabled = false`
- e prevista un'azione `delete` con semantics esplicita di governance

## Deliverables

- task di implementazione UI/admin proposal logic
- eventuale adeguamento contrattuale Core/API se necessario
- riallineamento minimo docs se il modello di governance cambia

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### Backend — `core/production_proposals/models.py`

`CoreProposalLogicConfig` esteso con colonna:
```python
disabled_logic_keys_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
```

### Backend — `alembic/versions/20260416_030_proposal_logic_disabled_keys.py`

Migrazione che aggiunge `disabled_logic_keys_json JSON NOT NULL DEFAULT '[]'` a `core_proposal_logic_config`.

### Backend — `core/production_proposals/config.py`

- `ProposalLogicConfig` esteso con `disabled_logic_keys: list[str] = []`
- `get_proposal_logic_config`: legge `disabled_logic_keys_json` dalla riga DB
- `set_proposal_logic_config`: accetta `disabled_logic_keys`, valida che nessuna chiave sconosciuta entri, e che la logica di default non sia mai disabilitata

### Backend — `app/api/admin.py`

- `SetProposalLogicConfigRequest`: aggiunto `disabled_logic_keys: list[str] = []`
- `put_proposal_logic_config`: passa `disabled_logic_keys` a `set_proposal_logic_config`
- `ProposalLogicConfigResponse` eredita da `ProposalLogicConfig`, quindi espone già `disabled_logic_keys`

### Backend — `app/api/produzione.py`

`get_proposal_logic_catalog`: il catalogo ritorna solo logiche abilitate:
```python
enabled_logics = [k for k in KNOWN_PROPOSAL_LOGICS if k not in config.disabled_logic_keys]
```
Così `ProduzioneHome` non può assegnare logiche disabilitate agli articoli.

### Frontend — `types/api.ts`

`ProposalLogicConfigResponse` esteso con `disabled_logic_keys: string[]`.

### Frontend — `AdminProposalLogicPage.tsx`

Completamente riscritto con layout a **2 colonne**:

- **Sinistra**: elenco `known_logics` con badge "Default" e "Disabilitata"; click per selezionare
- **Destra**: label, key mono, descrizione, sezione "Governance" con azioni, sezione "Parametri globali" con textarea JSON

**Azioni di governance** per logica selezionata:
- Toggle "Disabilita / Riabilita logica" — persiste `disabled_logic_keys`
- "Imposta come default" — solo se abilitata e non già default
- "Rimuovi dal catalogo articoli" — con dialog di conferma; semantics: disabilita (la logica resta nel registro)

**Guardrail**: la logica di default non può essere disabilitata (pulsanti disabilitati + testo esplicativo).

**Dialog delete**: mostra key, avvisa che gli articoli già configurati non vengono modificati automaticamente.

**Esito build:** `✓ built in 8.06s` — exit code 0.
