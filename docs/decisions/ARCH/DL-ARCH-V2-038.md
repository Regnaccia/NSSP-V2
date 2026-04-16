# DL-ARCH-V2-038 - Proposal full bar v2 with capacity-floor fallback

## Status
Accepted

## Date
2026-04-15

## Context

`proposal_full_bar_v1` usa una policy `strict_capacity`:

- prova una quantita a barre intere con arrotondamento `ceil`
- se sfora la capienza, ricade direttamente su `proposal_target_pieces_v1`

In alcuni casi stock-driven questo comportamento e troppo rigido:

- la proposta a `ceil` sfora la capienza
- ma una proposta a `floor` resterebbe a barre intere e starebbe sotto capienza

## Decision

Si introduce una nuova logica distinta:

- `proposal_full_bar_v2_capacity_floor`

Questa logica:

- conserva lo stesso modello `full bar`
- prova `ceil` come prima scelta
- se `ceil` sfora, tenta `floor`
- usa `floor` solo quando non compromette la copertura cliente

## Rules

### 1. Same raw-material model

La logica usa lo stesso modello della `proposal_full_bar_v1`:

- risoluzione del materiale grezzo via `materiale_grezzo_codice`
- `raw_bar_length_mm` letto sul materiale grezzo
- `usable_mm_per_piece` calcolato sul finito

### 2. Capacity-floor policy

Ordine di valutazione:

1. calcolare `qty_ceil`
2. se `qty_ceil` sta sotto capienza, usare `qty_ceil`
3. se `qty_ceil` sfora, calcolare `qty_floor`
4. usare `qty_floor` solo se:
   - `bars_floor > 0`
   - `availability_qty + qty_floor <= capacity_effective_qty`
   - se esiste `customer_shortage_qty`, `qty_floor >= customer_shortage_qty`
5. altrimenti fallback a `proposal_target_pieces_v1`

### 3. Customer safety

La logica non deve mai produrre una proposta inferiore alla copertura cliente necessaria.

Quindi:

- `floor` non e ammesso se porta sotto `customer_shortage_qty`

### 4. Boundary with v1

`proposal_full_bar_v2_capacity_floor` non sostituisce `proposal_full_bar_v1`.

Le due logiche restano entrambe valide:

- `v1` = `strict_capacity`
- `v2` = `ceil` then `capacity-floor`

## Consequences

### Positive

- piu casi restano a barra intera senza sforare la capienza
- il comportamento e piu utile nei casi stock-only
- la safety cliente resta preservata

### Tradeoffs

- il numero di logiche proposal aumenta
- serve diagnostica chiara per distinguere `v1` e `v2`

## Implementation Notes

Serve un task Core dedicato per:

- aggiungere la logica al registry
- implementare il tentativo `ceil -> floor`
- testare i casi stock-only e customer-driven
