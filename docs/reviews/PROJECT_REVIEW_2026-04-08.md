# ODE V2 - Project Review

## Date
2026-04-08

## Scope

Review critica trasversale dello stato V2 dopo il consolidamento di:

- stream `logistica`
- stream `produzione/articoli`
- stream `produzioni`
- `inventory`
- primo stream `ordini cliente`

Obiettivo:

- evidenziare i problemi potenziali piu rilevanti
- distinguerli dai semplici follow-up funzionali
- fissare una linea di risoluzione prima che la complessita cross-modulo cresca ulteriormente

## Sintesi

La V2 e in buona forma sul piano dei confini architetturali:

- `sync` separato da `core`
- Easy mantenuto `read-only`
- computed fact introdotti nel layer corretto
- primi stream verticali chiusi end-to-end

Il rischio principale non e piu definire nuovi pattern, ma rendere robusta l'orchestrazione tra:

- mirror sync
- fact derivati
- refresh on demand
- freshness percepita dalle surface

## Findings

### 1. Orchestrazione sequenziale non fail-fast

Se uno step di sync fallisce, i passi successivi possono ancora partire e produrre stato derivato su dati parziali o stantii.

Riferimenti:

- [sync_runner.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py#L117)
- [sync.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py#L232)

Rischio:

- rebuild o computed fact eseguiti anche dopo errori nei mirror upstream
- superficie dichiarata aggiornata anche se la catena non e stata completata in modo coerente

Direzione di risoluzione:

- introdurre `fail-fast` nelle catene con dipendenze
- oppure `skip_downstream_on_failed_prerequisite`
- esporre chiaramente il fallimento parziale nel risultato del refresh surface

### 2. Freshness delle surface incompleta rispetto ai fact derivati

Le freshness API oggi ragionano soprattutto sui mirror sync, ma alcune surface usano anche fact Core materializzati.

Riferimenti:

- [sync.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py#L97)
- [sync.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/api/sync.py#L243)
- [queries.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py#L140)

Rischio:

- una surface puo risultare `ready` mentre il computed fact che mostra non e stato ricostruito
- l'utente vede dati apparentemente freschi ma internamente incoerenti

Direzione di risoluzione:

- dare ai fact derivati un proprio freshness anchor
- oppure definire freshness composita per surface che dipendono da mirror + rebuild Core

### 3. Concorrenza sync ancora solo single-process

La guardia attuale usa lock in-memory ed e dichiaratamente adeguata solo a deployment single-process.

Riferimenti:

- [sync_runner.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py#L13)
- [sync_runner.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/sync_runner.py#L46)

Rischio:

- perdita della mutua esclusione con piu worker/processi
- collisioni future con scheduler automatico o deployment piu robusti

Direzione di risoluzione:

- introdurre lock distribuito o lease su DB prima di scheduler o multi-worker

### 4. Config condivisa non ancora completamente lazy-safe

Il refactor verso `get_settings()` e stato avviato correttamente, ma resta ancora un alias globale che materializza la config a import-time.

Riferimenti:

- [config.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/config.py#L40)
- [security.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/security.py#L13)
- [db.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/shared/db.py#L17)

Rischio:

- stato config fissato troppo presto nei test o nei bootstrap futuri
- comportamento meno prevedibile nei layer shared/auth

Direzione di risoluzione:

- rimuovere l'uso del singleton globale `settings`
- usare sempre `get_settings()` nei punti runtime

### 5. Alcuni read model stanno crescendo come full-scan in memoria

Oggi e ancora sostenibile, ma alcuni slice si stanno gia strutturando come letture complete seguite da aggregazione applicativa.

Riferimenti:

- [queries.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/ordini_cliente/queries.py#L116)
- [queries.py](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/core/articoli/queries.py#L76)

Rischio:

- degrado prestazionale quando `ordini`, `commitments` e `availability` entreranno davvero nelle surface
- pressione crescente su memoria e tempi risposta lato backend

Direzione di risoluzione:

- introdurre presto query paginabili e filtrabili server-side
- evitare che i prossimi slice di `commitments` nascano gia come scan completo globale

## Priorita consigliata

### Alta priorita

- robustezza delle catene di refresh con dipendenze
- coerenza freshness per computed fact derivati

### Media priorita

- rimozione dell'alias globale `settings`
- piano esplicito per concorrenza sync oltre il single-process

### Bassa ma da non rimandare troppo

- paginazione/filtri anche nei nuovi slice `ordini` e `commitments`

## Cosa non e un problema adesso

Non emergono oggi problemi strutturali sui confini principali:

- `sync` vs `core`
- pattern `mirror -> computed fact`
- uso di cataloghi interni
- modularita delle surface

La direzione architetturale resta corretta. I rischi aperti sono soprattutto di robustezza operativa e di scalabilita del modello runtime.

## Suggested Follow-up

1. Introdurre un task tecnico di hardening `sync chain orchestration`.
2. Introdurre un task tecnico su `freshness` dei fact Core derivati.
3. Inserire il cleanup finale di `shared.config` nei prossimi hardening task trasversali.
4. Considerare paginazione/filtri come requisito di default per tutti i nuovi slice oltre `customer_order_lines`.

## References

- [SYSTEM_OVERVIEW.md](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/SYSTEM_OVERVIEW.md)
- [STATUS.md](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/roadmap/STATUS.md)
- [IMPLEMENTATION_PATTERNS.md](c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/IMPLEMENTATION_PATTERNS.md)
