# TASK-V2-059 - Hardening criticita join article_code

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/task/TASK-V2-052-hardening-normalizzazione-article-code-cross-source.md`
- `docs/task/TASK-V2-055-criticita-articoli-v1.md`
- `docs/task/TASK-V2-056-refinement-ui-criticita-articoli.md`
- `docs/task/TASK-V2-057-toggle-considera-in-produzione-criticita.md`

## Goal

Correggere la vista `criticita articoli` affinche l'arricchimento con descrizione e famiglia funzioni anche per articoli il cui codice raw non coincide nel casing con la chiave canonica dei fact (`availability`, `commitments`, `inventory`, `customer_set_aside`).

## Context

Il slice `criticita` legge da `core_availability`, che usa `article_code` canonico normalizzato.

La query corrente arricchisce il dato con:

- `sync_articoli`
- `core_articolo_config`
- `articolo_famiglie`

ma lo fa joinando direttamente:

- `CoreAvailability.article_code == SyncArticolo.codice_articolo`
- `CoreAvailability.article_code == CoreArticoloConfig.codice_articolo`

Questo e fragile per articoli come `8x7x160`, dove:

- i fact canonici usano chiave normalizzata
- `sync_articoli` e `core_articolo_config` possono conservare il codice raw

Effetto pratico:

- la famiglia assegnata in `articoli` non viene vista dalla query `criticita`
- con `solo_in_produzione=true` l'articolo resta invisibile anche se la famiglia assegnata ha `considera_in_produzione=true`

Questo bug e distinto dal wiring del pulsante `Aggiorna` della vista `criticita`:

- `TASK-V2-058` copre il refresh completo della vista
- questo task copre l'allineamento corretto delle join cross-source

## Scope

### In Scope

- correggere le join cross-source del slice `criticita` usando la stessa chiave logica canonica dei fact
- riusare `normalize_article_code` o una strategia equivalente coerente con `TASK-V2-052`
- garantire che la famiglia assegnata da `articoli` sia visibile nella lista `criticita`
- garantire che il filtro `solo_in_produzione=true` includa articoli configurati la cui chiave raw differisce solo per casing/separazione dalla chiave canonica
- aggiungere test di regressione mirati sul caso reale di configurazione famiglia + criticita

### Out of Scope

- modifica della logica di criticita
- modifica della formula di `availability`
- redesign della vista UI
- nuovo refactor generale dei fact canonici

## Constraints

- non introdurre nuova semantica sui mirror `sync_*`
- mantenere `core_availability` come sorgente primaria della vista critica
- l'hardening deve essere coerente con la strategia gia introdotta in `TASK-V2-052`
- evitare nuovi confronti sparsi raw/case-sensitive nel slice `criticita`

## Refresh / Sync Behavior

La vista `criticita` riusa un refresh semantico backend gia esistente tramite la surface `produzione`.

Questo task non cambia la chain di refresh.

Corregge invece il fatto che, anche a dati freschi, la query puo perdere l'associazione articolo -> famiglia per mismatch tra chiave canonica e chiave raw.

## Acceptance Criteria

- un articolo con `availability_qty < 0` e famiglia assegnata con `considera_in_produzione=true` appare nella vista `criticita` anche se il suo codice raw nel mirror non coincide nel casing con la chiave canonica
- la famiglia assegnata dall'utente in `articoli` viene mostrata correttamente nella vista `criticita`
- il perimetro `solo_in_produzione=true` non esclude piu articoli validi per mismatch di join sul codice
- esistono test di regressione mirati sul caso mixed-case / raw-vs-canonical

## Deliverables

- hardening query/read model del slice `criticita`
- test di regressione dedicati
- completion notes con evidenza del bug corretto

## Verification Level

`Mirata`

Questo task corregge un bug localizzato di join cross-source nel slice `criticita`.

Quindi:

- test mirati backend sul core `criticita`
- build frontend solo se viene toccato il contratto o il wiring della vista
- niente full suite obbligatoria

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- trattare questo caso come estensione naturale di `TASK-V2-052`
- correggere le join del slice `criticita`, non solo i filtri
- aggiungere un test che riproduca esplicitamente:
  - articolo critico
  - famiglia assegnata via `core_articolo_config`
  - chiave raw != chiave canonica per semplice differenza di casing

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Root cause

`core_availability.article_code` è canonico (`strip().upper()`, scritto dal rebuild).
`sync_articoli.codice_articolo` e `core_articolo_config.codice_articolo` conservano il codice
raw così come arriva dalla sorgente o dalla UI (`set_famiglia_articolo`).

Con la join precedente:

```python
CoreAvailability.article_code == SyncArticolo.codice_articolo
CoreAvailability.article_code == CoreArticoloConfig.codice_articolo
```

un articolo come `"8x7x160"` (raw) vs `"8X7X160"` (canonical) non trovava corrispondenza.
Effetto: la famiglia non veniva vista, e con `solo_in_produzione=True` l'articolo era invisibile
anche se la famiglia aveva `considera_in_produzione=True`.

### Fix

`core/criticita/queries.py` — aggiunto `from sqlalchemy import func`. Le due join raw→canonical
usano ora `func.upper()` sul lato raw:

```python
.outerjoin(
    SyncArticolo,
    func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
)
.outerjoin(
    CoreArticoloConfig,
    func.upper(CoreArticoloConfig.codice_articolo) == CoreAvailability.article_code,
)
```

`func.upper()` è supportato sia da SQLite (test) che da PostgreSQL (produzione).
Il lato `CoreAvailability.article_code` è già canonico: nessun doppio UPPER necessario.

La strategia è coerente con TASK-V2-052 (normalizzazione cross-source al momento del rebuild),
ma applicata al lato query invece che al momento della scrittura — perché `sync_articoli`
e `core_articolo_config` non passano per un rebuild canonizzante.

### Test di regressione aggiunti

`tests/core/test_core_criticita.py` — 4 nuovi test (30 totali):

- `test_join_art_canonico_config_lowercase` — caso reale: availability `"8X7X160"`, sync_articoli
  e core_articolo_config con `"8x7x160"`, famiglia `considera_in_produzione=True`. Verifica
  che l'articolo sia incluso con la famiglia corretta (il test fallirebbe con il bug).
- `test_join_art_canonico_sync_lowercase` — descrizione arricchita correttamente con mismatch
  su sync_articoli.
- `test_join_toggle_false_con_mismatch_casing` — con `solo_in_produzione=False` e mismatch,
  la famiglia è visibile.
- `test_join_canonical_gia_uppercase_invariato` — baseline: chiave già canonica, comportamento
  invariato.

### Verifica

```
python -m pytest tests/core tests/app -q
294 passed in 5.02s
```

Frontend invariato — nessuna modifica al contratto API.

## Completed At

2026-04-10

## Completed By

Claude Code
