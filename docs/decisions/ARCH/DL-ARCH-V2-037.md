# DL-ARCH-V2-037 - Raw bar length belongs to raw-material articles

## Status
Accepted

## Date
2026-04-15

## Context

La prima modellazione di `proposal_full_bar_v1` assumeva che `raw_bar_length_mm` appartenesse all'articolo finito per cui viene generata la proposal.

La validazione operativa ha mostrato che questo e sbagliato.

Nel dominio reale:

- il finito espone `materiale_grezzo_codice`
- la lunghezza barra appartiene al materiale grezzo
- il calcolo `full bar` deve usare la barra del materiale associato, non del finito

## Decision

Si corregge il modello semantico:

- `raw_bar_length_mm` appartiene agli articoli materiale grezzo
- `proposal_full_bar_v1` parte dall'articolo finito
- risolve `materiale_grezzo_codice`
- legge `raw_bar_length_mm` sul materiale grezzo associato

## Rules

### 1. Ownership del dato barra

- `raw_bar_length_mm_enabled` va usato sulle famiglie di materiale grezzo per dire che il campo barra e pertinente
- `raw_bar_length_mm` va configurato sugli articoli materiale grezzo
- il finito non e il proprietario semantico del dato barra

### 2. Proposal full bar resolution

Per `proposal_full_bar_v1`:

- l'articolo proposal resta il finito
- `usable_mm_per_piece` resta calcolato sul finito usando:
  - `quantita_materiale_grezzo_occorrente`
  - `quantita_materiale_grezzo_scarto`
- `raw_bar_length_mm` viene letto sul materiale grezzo associato via `materiale_grezzo_codice`

### 3. Fallback

La logica fa fallback a pezzi anche se:

- il finito non risolve un `materiale_grezzo_codice` valido
- il materiale grezzo associato non ha `raw_bar_length_mm` configurato

### 4. Warning

Il warning `MISSING_RAW_BAR_LENGTH` va interpretato come warning del materiale grezzo:

- non del finito
- non della riga proposal
- ma dell'articolo che rappresenta la barra da lavorare

## Consequences

### Positive

- il modello riflette il dato reale di officina
- `proposal_full_bar_v1` usa la barra corretta
- il warning `MISSING_RAW_BAR_LENGTH` si allinea al vero proprietario del dato

### Tradeoffs

- la risoluzione proposal richiede un hop in piu: finito -> materiale grezzo
- le implementazioni gia fatte su finito vanno corrette

## Implementation Notes

Serve un task correttivo unico che riallinei:

- risoluzione `proposal_full_bar_v1`
- semantica del warning `MISSING_RAW_BAR_LENGTH`
- read model / payload diagnostici minimamente coerenti
