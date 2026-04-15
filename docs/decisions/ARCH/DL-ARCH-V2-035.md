# DL-ARCH-V2-035 - Proposal Full Bar V1

## Status
Accepted

## Date
2026-04-15

## Context

`Production Proposals` ha gia una prima logica minima `proposal_target_pieces_v1`, che propone esattamente i pezzi mancanti al target.

Serve ora una seconda logica V1 per articoli lavorati a barra intera, mantenendo:

- selezione logica a livello articolo
- config proposal governata da `admin` e visibile in `articoli`
- fallback sempre disponibile alla logica a pezzi

## Decision

Si introduce la seconda logica:

- `proposal_full_bar_v1`

e la si modella con queste regole.

### 1. Separazione tra famiglia e logica

La famiglia non decide quale logica proposal usare.

La famiglia introduce solo:

- `raw_bar_length_mm_enabled`

che significa:

- per questa famiglia ha senso configurare `raw_bar_length_mm`

Non significa:

- usare automaticamente la logica `proposal_full_bar_v1`

La scelta della logica resta a livello articolo tramite:

- `proposal_logic_key`

### 2. Configurazione articolo

Si introduce a livello articolo:

- `raw_bar_length_mm`

Questo campo e usato solo dalle logiche proposal che ne hanno bisogno, a partire da:

- `proposal_full_bar_v1`

### 3. Formula canonica

La logica barra intera usa:

```text
usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto
pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
bars_required = ceil(required_qty_total / pieces_per_bar)
proposed_qty = bars_required * pieces_per_bar
```

Il frammento note prodotto dalla logica e:

```text
BAR xN
```

dove `N = bars_required`.

### 4. Vincolo di capienza

La policy V1 e:

- `strict_capacity`

La logica full-bar e applicabile solo se:

```text
availability_qty + proposed_qty <= capacity_effective_qty
```

In V1:

- nessun overflow di capienza e ammesso

### 5. Fallback

`proposal_full_bar_v1` deve fare fallback a:

- `proposal_target_pieces_v1`

nei seguenti casi:

- `raw_bar_length_mm` mancante
- `usable_mm_per_piece <= 0`
- `pieces_per_bar <= 0`
- overflow di `capacity_effective_qty`
- qualunque situazione in cui la proposta a barre porterebbe a sotto-coprire `customer_shortage_qty`

Quindi:

- la logica barra non deve mai proporre meno di quanto serve a coprire il cliente

In V1:

- config mancante o non valida non blocca la proposal
- si fa fallback deterministico a pezzi

### 6. Warning

Si introduce un warning canonico nel modulo `Warnings`:

- `MISSING_RAW_BAR_LENGTH`

Condizione:

- `raw_bar_length_mm_enabled = true` sulla famiglia
- `raw_bar_length_mm` articolo mancante o `<= 0`

Questo warning:

- appartiene al modulo `Warnings`
- non e generato dalla logica proposal
- non seleziona automaticamente `proposal_full_bar_v1`
- segnala che il dato barra richiesto dal contratto famiglia-articolo non e configurato

Audience iniziale:

- `produzione`
- `admin`

## Consequences

### Positive

- la V1 proposal acquisisce una seconda logica utile e realistica
- il fallback a `proposal_target_pieces_v1` mantiene il sistema sempre utilizzabile
- famiglia, articolo e proposal logic restano separati in modo pulito

### Tradeoffs

- in V1 non vengono ancora modellati sfridi per barra, kerf o perdite fisse oltre `quantita_materiale_grezzo_scarto`
- in V1 non c'e ancora diagnostica esplicita del motivo di fallback proposal oltre al warning di configurazione mancante

## Implementation Notes

Servono quattro slice operative:

- modello/config per `raw_bar_length_mm_enabled` e `raw_bar_length_mm`
- UI famiglie per il nuovo flag
- UI articoli per il campo barra e la scelta della logica
- Core proposal logic `proposal_full_bar_v1`
- warning dedicato `MISSING_RAW_BAR_LENGTH`
