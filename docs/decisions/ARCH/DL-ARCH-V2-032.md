# DL-ARCH-V2-032 - Modello descrittivo unificato di Planning Candidates

## Status

Accepted

## Date

2026-04-14

## Context

`Planning Candidates` oggi usa due sorgenti descrittive diverse:

- nel ramo `by_article` la descrizione articolo sintetica del Core `articoli`
- nel ramo `by_customer_order_line` il segmento descrittivo della riga ordine, con eventuali
  righe di continuazione aggregate nel Core `ordini_cliente`

La semantica del ramo `by_customer_order_line` e piu ricca, ma il contratto planning non e ancora
uniforme:

- il ramo aggregato lavora gia con una descrizione "sintetica"
- il ramo per-riga ha bisogno di una descrizione completa
- la UI rischia di dover conoscere due modelli descrittivi diversi

## Decision

### 1. Il Core planning adotta un modello descrittivo canonico unico

Ogni `PlanningCandidate` deve convergere verso due campi descrittivi comuni:

- `description_parts: list[str]`
- `display_description: str`

### 2. Il ramo `by_customer_order_line` e il riferimento semantico del modello

La forma di riferimento del modello descrittivo e quella del ramo per-riga, perche e gia
strutturata in:

- segmento principale
- righe descrittive di continuazione

Regola:

- `by_customer_order_line`
  - `description_parts = [article_description_segment, ...description_lines]`

### 3. Il ramo `by_article` si riallinea allo stesso modello

Nel ramo aggregato il Core planning costruisce:

- `description_parts = [descrizione_1, descrizione_2]`

Questa lista deriva dal Core `articoli`, non da logiche UI.

### 4. Regole comuni di costruzione

Per entrambi i rami:

- i segmenti vuoti vengono rimossi
- l'ordine dei segmenti viene preservato
- `display_description` deriva da `description_parts`
- fallback finale:
  - `article_code` se `description_parts` e vuota

### 5. Compatibilita con i campi esistenti

I campi storici possono restare temporaneamente per compatibilita:

- `display_label`
- `order_line_description`
- `full_order_line_description`

Ma il target evolutivo e:

- UI e downstream leggono `display_description`
- `description_parts` resta disponibile come forma strutturata

## Consequences

### Positive

- la UI planning legge un solo contratto descrittivo canonico
- il ramo `by_customer_order_line` non perde piu la struttura descrittiva ricca
- il ramo `by_article` si allinea senza inventare una falsa semantica ordine-cliente
- futuri moduli come `Production Proposals` ricevono gia un modello coerente

### Tradeoffs

- il read model planning cresce di due campi
- servira una fase di compatibilita con i campi descrittivi gia esistenti

## Out of Scope

- regole tipografiche UI
- badge famiglia o motivi
- destinazione richiesta
- `earliest_uncovered_due_date`

## References

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`
