# TASK-V2-094 - Admin stock logic dedicated section and capacity params

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
- `docs/task/TASK-V2-090-admin-stock-logic-config.md`
- `docs/task/TASK-V2-092-fix-capacity-from-containers-v1-legacy-formula.md`

## Goal

Rifinire la governance admin delle logiche stock, separandola chiaramente dalla gestione utenti e rendendo configurabili anche i parametri della logica fissa `capacity_from_containers_v1`.

## Context

La surface `admin` espone gia una sezione stock logic, ma oggi:

- e ancora aggregata nella stessa pagina utenti
- non costituisce una sezione di governance chiaramente separata
- non permette un tuning esplicito dei `capacity_logic_params`

Con il fix di `capacity_from_containers_v1` diventa necessario rendere governabile almeno:

- `max_container_weight_kg`

senza mischiare questa configurazione con l'area utenti/ruoli.

## Scope

- riorganizzare la surface `admin` in modo che la configurazione stock logic viva in una sezione dedicata, non aggregata visivamente alla gestione utenti
- esporre e rendere modificabili i `capacity_logic_params`
- supportare almeno il parametro V1:
  - `max_container_weight_kg`
- mantenere distinta la governance di:
  - strategy e params `monthly_stock_base_*`
  - parametri della logica fissa `capacity_from_containers_v1`
- aggiornare testi e labeling per chiarire:
  - cosa e modificabile
  - cosa e fisso come `logic_key`
  - cosa e solo parametro della logica fissa

## Refresh / Sync Behavior

- La surface `admin` non introduce un refresh semantico backend nuovo
- Dopo il salvataggio, la sezione dedicata deve riflettere la configurazione aggiornata
- I ricalcoli operativi restano demand-driven dalle surface che consumano le metriche stock

## Out of Scope

- modificare la formula Core di capacity (coperto da `TASK-V2-092`)
- introdurre nuove strategy capacity switchabili
- configurazione default/override articolo o famiglia

## Constraints

- `capacity_logic_key` resta fisso e non switchabile
- i parametri capacity devono essere coerenti col contratto Core esistente
- la sezione stock logic deve essere chiaramente distinta dalla gestione utenti

## Acceptance Criteria

- `admin` mostra una sezione dedicata alle logiche stock separata dalla gestione utenti
- `capacity_logic_params` sono visibili e modificabili
- `max_container_weight_kg` e governabile da UI
- il `capacity_logic_key` resta non modificabile ma chiaramente visibile

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```powershell
python -m pytest tests/ -v
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Riorganizzato `AdminHome.tsx`: utenti e logiche stock ora sono due `<section>` distinte con heading e `space-y-10` tra loro (non più `<hr>` senza titolo)
- La sezione "Logiche stock V1" ha header con titolo e descrizione esplicita
- Aggiunto campo `max_container_weight_kg` nella sezione capacity di `StockLogicConfigSection`: input numerico step 0.5, caricato da `capacity_logic_params` e incluso nel PUT
- La sezione capacity mostra formula `capacity = max_container_weight_kg × contenitori / (peso_grammi / 1000)` come riferimento
- `capacity_logic_key` rimane visibile come badge read-only (`Fisso` → rimosso, ora inline col titolo section)
- `buildCapacityParams()` costruisce `{max_container_weight_kg: v}` se il valore è valido; il backend riceve params coerenti col contratto Core
- 851 test verdi

## Completed At

2026-04-13

## Completed By

Claude Code
