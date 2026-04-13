# TASK-V2-073 - Fix sync_mag_reale: re-bootstrap completo

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/reviews/BUG-MAG-REALE-DELETE-HANDLING-2026-04-10.md`

## Goal

Riallineare il mirror `sync_mag_reale` con la fonte Easy eliminando i movimenti
fantasma (eliminati/rettificati in Easy ma presenti nel mirror ODE).

## Context

Il sync `mag_reale` usa la strategia `append_only` con `DELETE_HANDLING = "no_delete_handling"`.

Easy ha eliminato o rettificato almeno 27 movimenti già importati nel mirror ODE.
Questi movimenti fantasma causano una divergenza di giacenza (+200 scarichi fittizi
per articolo `18X11X125R`), producendo disponibilità errate nella UI e nei Planning
Candidates.

Il mirror ODE ha **337.944 righe** vs **337.917 righe** in Easy — 27 righe in più
nel mirror che non esistono più in Easy.

## Scope

- truncate completo di `sync_mag_reale`
- re-sync da cursor=0 (tutti i movimenti da Easy)
- rebuild `core_inventory_positions`
- rebuild `core_availability` (e chain dipendenti: `customer_set_aside`, `commitments`)
- verifica post-fix: confronto giacenza `18X11X125R` tra ODE e Easy
- aggiungere script `scripts/rebootstrap_mag_reale.py` che esegue la sequenza

## Out of Scope

- modificare la strategia di sync (da `append_only` a `full_replace` o `reconcile`)
  — quello è il fix architetturale di lungo termine, richiede DL-ARCH separato
- fix automatico delle rettifiche future — il problema si ripresenterà a lungo
  andare; questo task risolve solo l'accumulo attuale

## Constraints

- il truncate di `sync_mag_reale` deve avvenire in una transazione controllata
- il re-sync deve essere eseguito con cursor=0 esplicito (override del cursor
  automatico che leggerebbe da `sync_entity_state`)
- il rebuild della chain deve avvenire nell'ordine corretto:
  `mag_reale` → `inventory_positions` → `customer_set_aside` → `commitments` → `availability`
- durante il re-import la superficie dati non è affidabile — eseguire fuori orario
  operativo se possibile

## Acceptance Criteria

- `sync_mag_reale` ha lo stesso numero di righe di Easy MAG_REALE (o differenza ≤ 1
  per movimenti aggiunti durante il re-import)
- `core_inventory_positions` per `18X11X125R` mostra `on_hand_qty = +25` (o valore
  allineato con Easy)
- `core_availability` per `18X11X125R` mostra `availability_qty` coerente con Easy
- nessun altro articolo mostra divergenza sistematica di giacenza dopo il fix

## Verification Level

- `Mirata`

Verifiche minime:

- confronto diretto Easy vs ODE per `18X11X125R` dopo il fix
- confronto conteggio righe `sync_mag_reale` vs Easy MAG_REALE totale
- `scripts/inspect_availability.py 18X11X125R` mostra differenza ODE vs Easy = 0

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

## Completion Notes

TASK-V2-073 completato. Re-bootstrap eseguito in sequenza completa:

- Eliminati **337.944** record da `sync_mag_reale` (mirror precedente, con 27 righe fantasma)
- Re-importati **337.917** movimenti da Easy (allineamento esatto)
- Rebuild chain: 2.297 posizioni inventory, 94 set_aside, 226 commitments, 2.297 availability

Articolo campione `18X11X125R`:
- **Prima**: `availability_qty = -175` (ODE), Easy = +25, divergenza = -200
- **Dopo**: `availability_qty = +25` (ODE), Easy = +25, divergenza = 0 [OK]

Script aggiunto: `scripts/rebootstrap_mag_reale.py` — riutilizzabile per future correzioni
manuali della stessa natura.

## Verification Notes

Verifica post-fix inline nello script:

```
inventory_qty     :     25.000
set_aside_qty     :      0.000
committed_qty     :      0.000
availability_qty  :     25.000
Easy giacenza     :     25.000
Differenza ODE-Easy:     0.000  [OK]
```

Conteggio righe: Easy 337.917 — ODE post-fix 337.917 (allineamento esatto).

## Completed At

2026-04-10

## Completed By

Claude Code
