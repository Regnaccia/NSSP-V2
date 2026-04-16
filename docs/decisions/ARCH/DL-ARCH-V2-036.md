# DL-ARCH-V2-036 - Proposal logic diagnostics and fallback traceability

## Status
Accepted

## Date
2026-04-15

## Context

Con l'introduzione di piu logiche proposal, una riga del workspace puo:

- richiedere una logica sull'articolo
- essere calcolata con una logica effettiva diversa
- ricadere su fallback deterministici

Senza diagnostica esplicita, la UI `Production Proposals` mostra solo il risultato finale e rende opaco capire:

- se `proposal_full_bar_v1` sia stata davvero applicata
- se sia ricaduta su `proposal_target_pieces_v1`
- per quale motivo tecnico o di dominio

## Decision

Si introduce una diagnostica locale al modulo `Production Proposals`.

Campi minimi:

- `requested_proposal_logic_key`
- `effective_proposal_logic_key`
- `proposal_fallback_reason`

## Rules

### 1. Requested vs effective logic

- `requested_proposal_logic_key` riflette la logica configurata sull'articolo
- `effective_proposal_logic_key` riflette la logica realmente usata per calcolare `proposed_qty`

### 2. Fallback reason

Se la logica richiesta non puo essere applicata, il modulo proposal deve fare fallback deterministico e valorizzare:

- `proposal_fallback_reason`

Vocabolario iniziale:

- `missing_raw_bar_length`
- `invalid_usable_mm_per_piece`
- `pieces_per_bar_le_zero`
- `capacity_overflow`
- `customer_undercoverage`

### 3. Boundary with Warnings

Questa diagnostica:

- non appartiene al modulo `Warnings`
- non deve generare warning canonici globali
- serve solo a spiegare il comportamento interno della proposal logic

Il warning canonico `MISSING_RAW_BAR_LENGTH` resta valido e separato, ma non sostituisce `proposal_fallback_reason`.

### 4. UI expectation

La UI `Production Proposals` deve poter mostrare almeno:

- logica richiesta
- logica effettiva
- motivo del fallback quando presente

## Consequences

### Positive

- la quantita proposta diventa spiegabile direttamente dalla UI
- il debug operativo dei casi `full bar -> pezzi` non richiede piu indagine indiretta
- il modulo `Warnings` resta pulito e separato dalla diagnostica locale proposal

### Tradeoffs

- il contratto proposal si arricchisce di metadati tecnici aggiuntivi
- la UI deve trovare un rendering leggibile senza appesantire troppo la tabella principale

## Implementation Notes

Servono due slice dedicate:

- Core/API per requested/effective/fallback reason
- UI `Production Proposals` per mostrare la diagnostica locale
