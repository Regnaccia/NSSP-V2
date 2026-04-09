# TASK-V2-052 - Hardening normalizzazione article_code cross-source

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/task/TASK-V2-037-core-inventory-positions.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`
- `docs/task/TASK-V2-043-commitments-produzione.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`
- `docs/task/TASK-V2-049-core-availability.md`
- `docs/task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-051-refresh-sequenziale-articoli-con-availability.md`

## Goal

Completare l'hardening dei confronti `article_code` cross-source usando una normalizzazione condivisa unica, senza cambiare la semantica dei mirror `sync_*`.

## Context

Il bug emerso nel calcolo di `availability` ha mostrato che lo stesso articolo poteva vivere con chiavi diverse tra fact canonici:

- `inventory_positions`
- `customer_set_aside`
- `commitments`
- `availability`

Questo produceva split logici del tipo:

- `8x7x40`
- `8X7X40`

con effetti concreti sul dettaglio `articoli`, dove i contributi provenivano da record diversi e la disponibilita poteva risultare falsa.

Il fix immediato e gia stato applicato sul percorso critico tramite:

- helper condivisa `normalize_article_code`
- rebuild canonici `customer_set_aside`, `commitments`, `availability`
- lookup del dettaglio `articoli`

Resta ora il follow-up di hardening leggero:

- sostituire i confronti `article_code` cross-source residui con la helper condivisa
- evitare nuovi `strip().upper()` sparsi
- mantenere invariata la vicinanza dei mirror alla sorgente Easy

## Scope

- censire i confronti `article_code` cross-source ancora presenti nel backend
- sostituire i casi residui con `normalize_article_code`
- usare la helper condivisa nei layer `core` e nelle query/fact che uniscono dati da piu sorgenti
- evitare duplicazioni locali della regola di normalizzazione
- aggiornare test dove serve per coprire codici misti (`raw`, trim, lowercase, uppercase)
- aggiornare la documentazione tecnica minima del pattern

## Out of Scope

- cambiare la semantica dei mirror `sync_*`
- forzare la normalizzazione persistente di tutti i campi raw in ingresso dalle sorgenti Easy
- ridefinire `source identity`
- introdurre un nuovo `DL-ARCH`
- modificare formati UI o etichette utente

## Constraints

- i mirror `sync_*` restano vicini alla sorgente e possono conservare il dato raw/trimmed gia previsto dai rispettivi mapping
- la normalizzazione condivisa va usata dove il codice articolo diventa chiave logica cross-source
- non introdurre nuove semantiche oltre a:
  - trim esterno
  - uppercase
  - stringa vuota -> `None`
- i fact canonici gia materializzati devono continuare a poter essere ricostruiti integralmente

## Acceptance Criteria

- i confronti `article_code` cross-source residui nel backend usano `normalize_article_code` o un join equivalente coerente con essa
- non restano nuovi confronti logici sparsi basati su `strip().upper()` fuori dalla helper condivisa, salvo motivazione esplicita
- i test backend coprono almeno un caso mixed-case/trim per ogni percorso critico rimasto aperto
- il task documenta chiaramente che il fix availability/set_aside/commitments gia eseguito diventa regola di hardening generale
- `python -m pytest tests/core -q` passa

## Deliverables

- hardening codice backend sui confronti `article_code` cross-source residui
- eventuali test di regressione aggiuntivi
- aggiornamento documentazione tecnica/pattern

## Verification Level

`Mirata`

Questo task e un hardening selettivo dei confronti cross-source e non una milestone architetturale.

Quindi:

- non richiede full suite obbligatoria
- richiede test backend mirati sui percorsi `core` che usano `article_code` come chiave logica cross-source
- la verifica deve restare proporzionata ai punti effettivamente toccati

## Verification Commands

```bash
cd backend
python -m pytest tests/core -q
```

Output atteso:

- exit code `0`
- nessuna regressione sui fact `inventory`, `customer_set_aside`, `commitments`, `availability`

## Implementation Notes

Direzione raccomandata:

- riusare sempre `src/nssp_v2/shared/article_codes.py`
- distinguere esplicitamente:
  - confronto tecnico cross-source -> helper condivisa
  - dato mirror vicino alla sorgente -> invariato
- preferire fix piccoli e mirati ai layer `core` / query / fact / join applicativi

---

## Completion Notes

### Censimento confronti cross-source residui

Analisi dei confronti `article_code` cross-source nel backend al momento del task:

| Layer | File | Stato prima del task |
|---|---|---|
| `core/commitments/queries.py` | `rebuild_commitments` + `list_commitments` | OK — usa `normalize_article_code` |
| `core/customer_set_aside/queries.py` | `rebuild_customer_set_aside` + `list_customer_set_aside` | OK — usa `normalize_article_code` |
| `core/availability/queries.py` | `rebuild_availability` + `get_availability` | OK — usa `normalize_article_code` |
| `core/articoli/queries.py` | `get_articolo_detail` (join cross-fact) | OK — usa `normalize_article_code` |
| `core/inventory_positions/queries.py` | `rebuild_inventory_positions` + `get_inventory_position` | **GAP** — mancava `normalize_article_code` |
| `core/ordini_cliente/queries.py` | read model da singola sorgente | OK — nessun confronto cross-source |
| `sync/mag_reale/source.py` | `_normalize_codice_articolo` locale | OK — layer sync, vicino alla sorgente (invariato per design) |
| `sync/righe_ordine_cliente/source.py` | `_strip_or_none` per `article_code` | OK — layer sync, vicino alla sorgente (invariato per design) |

### File modificati

**Backend:**

- `src/nssp_v2/core/inventory_positions/queries.py`
  - Aggiunto import `normalize_article_code`
  - In `rebuild_inventory_positions`: `article_code=normalize_article_code(row.codice_articolo)` con guard `if article_code is None: continue` prima dell'insert
  - In `get_inventory_position`: input normalizzato con `normalize_article_code` prima del filtro; ritorna `None` se il codice normalizzato è None

- `tests/core/test_core_inventory_positions.py`
  - Aggiunti 5 test nella sezione `Normalizzazione article_code cross-source (TASK-V2-052)`:
    - `test_rebuild_normalizza_lowercase`
    - `test_rebuild_normalizza_spazi_esterni`
    - `test_rebuild_chiave_canonica_con_codice_misto`
    - `test_get_inventory_position_normalizza_input_lowercase`
    - `test_get_inventory_position_normalizza_input_con_spazi`

### Perché il gap era solo in inventory_positions

I fact `customer_set_aside` e `commitments` usano `normalize_article_code` al momento del rebuild (introdotto durante il debug del bug disponibilità). Il fact `availability` normalizza i codici quando legge dai fact sorgente. Il Core `articoli` normalizza prima di filtrare i fact correlati.

`inventory_positions` era rimasto indietro perché il bug originale aveva impatto solo sull'incrocio `set_aside / commitments / availability`, non sull'inventory che si aggiornava indipendentemente.

### Limite noto: GROUP BY avviene prima della normalizzazione Python

Il rebuild di `inventory_positions` esegue la `GROUP BY codice_articolo` in SQL prima di normalizzare in Python. Se il mirror contenesse lo stesso articolo con casing diverso (`art001` e `ART001`), il rebuild produrrebbe due righe SQL che entrambe normalizzano a `ART001` → UniqueConstraint violation.

Questo scenario non si verifica in produzione perché il sync `mag_reale` normalizza già `codice_articolo` a ingestione (`_normalize_codice_articolo` in `source.py`). Il limite è accettabile nel V1.

Se in futuro il sync venisse modificato o dati venissero migrati senza normalizzazione, il rebuild dovrebbe aggregare in Python dopo la normalizzazione. Documentato come follow-up.

### Test eseguiti

`python -m pytest tests/core -q`: 249/249 passed.

### Assunzioni

- Il sync `mag_reale` già normalizza `codice_articolo` in ingresso — il fix a livello Core è difensivo e garantisce la chiave canonica anche in scenari di test o migrazione non canonici.
- I mirror `sync_*` restano invariati: la normalizzazione non viene applicata ai layer sync.

### Follow-up suggeriti

- Se il sync `mag_reale` venisse modificato per accettare dati senza normalizzazione, il rebuild `inventory_positions` dovrebbe aggregare i codici normalizzati in Python (dict) invece di affidarsi al GROUP BY SQL.

## Completed At

2026-04-09

## Completed By

Claude Code
