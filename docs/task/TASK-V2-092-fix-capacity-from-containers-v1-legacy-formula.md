# TASK-V2-092 - Fix capacity_from_containers_v1 legacy formula

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date
2026-04-13

## Owner
Claude Code

## Source Documents

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
- `docs/task/TASK-V2-084-core-stock-policy-metrics-v1.md`
- `docs/task/TASK-V2-089-ui-articoli-stock-policy-metrics.md`

## Goal

Riallineare `capacity_from_containers_v1` alla formula legacy concordata, in modo che
`capacity_calculated_qty` rappresenti una vera capienza calcolata e non il semplice parsing di `ART_CONTEN`.

## Context

Lo stato attuale espone `capacity_calculated_qty` nella surface `articoli` e la usa
nelle metriche stock, ma l'implementazione corrente:

- legge `contenitori_magazzino`
- fa solo parsing numerico del valore
- ignora `peso_grammi`

Questo crea un delta semantico rispetto al comportamento legacy gia analizzato, dove la
capienza veniva stimata a partire da:

- numero contenitori (`ART_CONTEN`)
- peso articolo (`ART_KG`)
- peso massimo contenitore configurabile

Quindi oggi il dato esposto come `capacity_calculated_qty` puo essere formalmente coerente
col codice, ma non col significato operativo atteso.

## Scope

- aggiornare la logica `capacity_from_containers_v1` nel Core stock policy
- supportare il parsing di `ART_CONTEN` nei casi:
  - intero
  - decimale
  - stringa frazionaria tipo `a/b`
- usare anche `peso_grammi` / `ART_KG` nel calcolo della capienza
- applicare la formula legacy V1:
  - `capacity_calculated_qty = max_container_weight_kg * containers / article_weight_kg`
- leggere `max_container_weight_kg` dai parametri config gia previsti
- chiarire i fallback quando:
  - `ART_CONTEN` e invalido
  - `ART_KG` e nullo / zero / invalido
- aggiornare test di logica e test integrazione stock policy
- aggiornare la documentazione locale del task se cambiano dettagli di formula o fallback

## Out of Scope

- introdurre una nuova strategy selezionabile per la capacity
- cambiare il contratto UI di `articoli`
- introdurre warning badge o modifiche a `Planning Candidates`
- ridefinire `capacity_override_qty`
- cambiare il significato di `capacity_effective_qty`

## Constraints

- `capacity_from_containers_v1` resta una logica fissa, non switchabile
- i dati sorgente devono continuare a provenire solo da:
  - `sync_articoli`
  - config interna V2
- nessuna lettura diretta da Easy
- la formula deve essere esplicita e testata
- se i dati non consentono un calcolo affidabile, `capacity_calculated_qty` deve restare `None`

## Refresh / Sync Behavior

- La vista `articoli` riusa il refresh semantico backend gia esistente della surface `articoli`
- Il task non introduce un nuovo refresh separato
- Le metriche corrette devono risultare visibili dopo il normale refresh / reload dei dettagli articolo

## Acceptance Criteria

- `capacity_calculated_qty` non coincide piu con il semplice parsing di `ART_CONTEN`
- la formula usa sia contenitori sia peso articolo
- `ART_CONTEN` frazionario tipo `a/b` viene interpretato correttamente
- `ART_KG` nullo/zero/non valido produce `capacity_calculated_qty = None`
- `capacity_effective_qty` continua a rispettare la precedenza:
  - override articolo
  - altrimenti calculated
- i test Core stock policy coprono i nuovi casi di formula e fallback

## Verification Level

- `Mirata`

## Environment Bootstrap

```powershell
cd V2/backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Verification Commands

```powershell
$env:DEBUG='false'; .\.venv\Scripts\python -m pytest V2/backend/tests/core/test_core_stock_policy_logic.py V2/backend/tests/core/test_core_stock_policy_metrics.py -q
```

Output atteso:

- test verdi
- nuovi casi `capacity_from_containers_v1` coperti

## Implementation Notes

- riferimento legacy analizzato:
  - `C:\Users\Alberto.REGNANI\Desktop\Python\Django\Regnani_V4\Ufficio\Utilita\Elenco_articoli.py`
- nel legacy:
  - `ART_CONTEN` veniva normalizzato anche nel caso `a/b`
  - `ART_KG` entrava nella formula
  - `max_peso_contenitore` era un parametro numerico oggi da leggere da config
- evitare sentinel legacy tipo `1e9`
- in V2 il fallback corretto e `None`, non valori fittizi

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Aggiunto `_parse_contenitori` in `logic.py`: parsa intero, decimale, frazione `a/b`; restituisce `None` se non valido o ≤ 0
- Riscritta `estimate_capacity_from_containers_v1` con formula legacy: `max_container_weight_kg * containers / (peso_grammi / 1000)`
- Fallback `None` se `peso_grammi` assente/zero o `max_container_weight_kg` non in params
- Aggiornata call in `queries.py` per passare `art.peso_grammi` e `dict(config.capacity_logic_params)`
- 12 unit test per `_parse_contenitori` + 13 test formula in `test_core_stock_policy_logic.py`
- Integration test `test_target_limitato_da_capacity` aggiornato: usa `contenitori="1"`, `peso_grammi=Decimal("500")` → capacity = 50
- 112 test verdi

## Completed At

2026-04-13

## Completed By

Claude Code
