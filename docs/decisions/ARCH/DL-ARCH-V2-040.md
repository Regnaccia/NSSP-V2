# DL-ARCH-V2-040 - Planning candidates rebase: need vs release-now contract

## Status
Active

## Date
2026-04-15

## Context

Il rebase architetturale della V2 ha fissato che `Planning Candidates` non deve piu esporre una sola quantita implicita.

Il caso tipico e:

- bisogno futuro reale presente
- magazzino attuale gia prossimo alla saturazione
- nuova produzione teoricamente utile in futuro
- ma non lanciabile ora senza overflow

Il legacy V4 distingueva gia questi due piani con la logica:

```text
da_produrre = min(cap_residua, prod_a_scorta)
```

La V2 deve quindi separare:

- `need detection`
- `release feasibility now`

senza spostare questa distinzione dentro `Production Proposals`.

## Decision

Il primo stream del rebase planning introduce un contratto esplicito `need vs release now`.

## Contract

### 1. Quantita di bisogno

Nuovo campo:

- `required_qty_eventual`

Semantica:

- quantita mancante rispetto al bisogno futuro/target
- non implica automaticamente che la stessa quantita sia lanciabile ora

Nel primo slice:

- sul ramo `by_article`, `required_qty_eventual` coincide con il bisogno aggregato oggi gia espresso da `required_qty_total`
- i campi storici restano visibili per compatibilita

### 2. Headroom attuale di capienza

Nuovo campo intermedio nel read model `by_article`:

- `capacity_headroom_now_qty`

Formula V1 del rebase:

```text
capacity_headroom_now_qty = max(capacity_effective_qty - inventory_qty, 0)
```

Regola:

- il confronto per il rilascio immediato usa la giacenza fisica attuale, non la sola `availability_qty`
- questo evita proposte "lanciabili ora" quando il magazzino e gia saturo ma il netto disponibile e positivo per via degli impegni futuri

### 3. Quantita lanciabile ora

Nuovo campo:

- `release_qty_now_max`

Formula V1 del rebase sul ramo `by_article`:

```text
release_qty_now_max = min(required_qty_eventual, capacity_headroom_now_qty)
```

### 4. Stato di rilascio

Nuovo campo:

- `release_status`

Vocabolario iniziale:

- `launchable_now`
- `launchable_partially`
- `blocked_by_capacity_now`

Regole:

- `launchable_now`
  - `release_qty_now_max >= required_qty_eventual`
- `launchable_partially`
  - `0 < release_qty_now_max < required_qty_eventual`
- `blocked_by_capacity_now`
  - `release_qty_now_max = 0` e `required_qty_eventual > 0`

## Scope del primo slice

Il primo slice implementativo del rebase vale in modo completo per:

- `Planning Candidates by_article`

Per il ramo:

- `by_customer_order_line`

la distinzione `need vs release now` non viene ancora resa quantitativa in modo pieno in questo primo stream, per evitare duplicazione ambigua della stessa capienza articolo su piu righe cliente.

Compatibilita del ramo per-riga nel primo slice:

- i campi storici restano invariati
- i nuovi campi possono essere assenti o `null`
- il rebase quantitativo completo del ramo per-riga verra trattato in un secondo slice esplicito

## Consequences

### Positive

- `Planning Candidates` smette di confondere il bisogno con la lanciabilita immediata
- i casi di magazzino saturo restano visibili come need ma non risultano falsamente rilasciabili
- `Production Proposals` puo consumare una semantica piu pulita senza reinventare la capienza

### Constraints

- il primo slice non deve rompere i campi attuali:
  - `required_qty_minimum`
  - `required_qty_total`
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `primary_driver`
- il ramo `by_customer_order_line` non va forzato prematuramente in un modello di rilascio aggregato non ancora deciso
