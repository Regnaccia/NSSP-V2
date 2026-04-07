# DL-ARCH-V2-009 - Sync unit contract

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

`DL-ARCH-V2-007` ha introdotto il modello di sincronizzazione per entita,
mentre `DL-ARCH-V2-008` ha definito il modello di esecuzione runtime e freshness.

Per poter implementare le prime unita di sync, ad esempio clienti e destinazioni,
in modo coerente e scalabile, e necessario definire un contratto minimo
che ogni unita di sync deve rispettare.

Senza questo contratto, il rischio e:

- implementazioni incoerenti tra entita diverse
- difficolta nel garantire idempotenza e allineamento corretto
- confusione tra responsabilita di Sync e Core
- incompatibilita con scheduling, freshness e orchestrazione

## Decision

La V2 introduce un contratto minimo obbligatorio per ogni unita di sync per entita.

Ogni unita di sync e considerata valida solo se dichiara esplicitamente:

- identita della sorgente
- ownership del target interno
- strategia di allineamento
- modalita di acquisizione cambiamenti
- metadati di esecuzione
- policy di gestione delete
- dipendenze

## 1. Ownership del target interno

Ogni unita di sync possiede un target interno dedicato.

Il target puo essere modellato come:

- mirror interno
- staging interno owned dalla sync unit

Per i primi slice il pattern consigliato e il mirror interno, ma il DL non impone che tutte le implementazioni future usino solo mirror puri.

Regola:

- una sync unit scrive esclusivamente nel proprio spazio di persistenza
- altre sync unit non devono scrivere su tale spazio
- il Core puo leggere, ma non deve governare direttamente il target sync

Il target della sync non coincide con il modello Core.

## 2. Source identity (upsert key)

Ogni unita deve dichiarare la chiave di identita della sorgente.

Esempi:

- clienti -> `CLI_COD`
- destinazioni -> `(CLI_COD, NUM_PROGR_CLIENTE)`

Questa chiave e utilizzata per:

- upsert
- deduplicazione
- idempotenza

Regola:

> Nessuna unita di sync e valida senza una source identity esplicita.

## 3. Alignment strategy

Ogni unita deve dichiarare come allinea il target interno alla sorgente.

Strategie possibili:

- `full_replace`
- `upsert`
- `upsert_with_delete_reconciliation`
- `append_only` (futuro)

Default consigliato:

- `upsert` con eventuale gestione delete coerente

Regola:

> La strategia di allineamento deve essere dichiarata e non implicita.

## 4. Change acquisition strategy

Ogni unita deve dichiarare come acquisisce i dati dalla sorgente.

Strategie possibili:

- `full_scan`
- `watermark`
- `cursor`
- `external_change_token`

Nella fase iniziale e accettato `full_scan`,
ma la strategia deve essere esplicitata.

## 5. Delete handling policy

Ogni unita deve dichiarare come gestisce i record non piu presenti nella sorgente.

Strategie possibili:

- `hard_delete`
- `soft_delete`
- `mark_inactive`
- `no_delete_handling`

Regola:

> L'assenza dalla sorgente deve avere un comportamento definito.

## 6. Run metadata contract

Ogni esecuzione della sync deve produrre metadati minimi di run:

- `run_id`
- `started_at`
- `finished_at`
- `status`
- `rows_seen`
- `rows_written`
- `rows_deleted` (se applicabile)
- `error_message` (se fallita)

Questi metadati supportano:

- osservabilita
- debugging
- audit tecnico minimo

## 7. Freshness anchor

Ogni unita deve esporre almeno uno stato sintetico corrente usato come anchor di freshness.

Minimo richiesto:

- `last_success_at`

Questo valore e utilizzato per:

- valutare la freschezza dei dati
- supportare le policy di refresh delle surface definite in `DL-ARCH-V2-008`

Regola:

- i metadati di run descrivono singole esecuzioni
- il freshness anchor descrive lo stato corrente della sync unit

## 8. Dependency declaration

Ogni unita puo dichiarare dipendenze da altre unita di sync.

Esempi:

- destinazioni dipende da clienti
- ordini dipende da clienti e articoli

Le dipendenze:

- devono essere esplicite
- sono utilizzate dall'orchestrator definito in `DL-ARCH-V2-008`

## 9. Mirror vs Core separation

Il target della sync e un target interno vicino alla sorgente, non il modello operativo del Core.

Regole:

- il target sync mantiene struttura e semantica vicine alla sorgente
- non deve essere progettato per la UI
- non deve includere logiche di business

Il Core:

- costruisce relazioni tra entita
- introduce dati interni quando servono
- produce il modello operativo

Regola fondamentale:

> La sync trasferisce dati; il core costruisce significato.

## 10. Idempotenza

Ogni unita deve essere idempotente.

Eseguire la sync piu volte con lo stesso stato della sorgente:

- non deve produrre duplicazioni
- non deve generare inconsistenze

## Esclusioni (out of scope)

Questo DL NON definisce:

- struttura fisica delle tabelle (DDL specifico)
- tecnologia di persistenza
- implementazione dello scheduler
- retry policy avanzate
- gestione distribuita
- dettaglio di orchestrazione runtime

## Consequences

### Positive

- uniformita tra tutte le unita di sync
- maggiore robustezza e prevedibilita
- compatibilita con scheduling e freshness model
- chiara separazione Sync/Core

### Negative / Trade-off

- maggiore disciplina richiesta in fase di implementazione
- necessita di definire esplicitamente ogni unita

## Impatto sul progetto

Questo DL e riferimento per:

- implementazione delle prime sync (clienti, destinazioni)
- progettazione dei target interni sync
- task di integrazione con Easy

E prerequisito per:

- primi task sync clienti e destinazioni
- definizione dei target mirror o staging per entita

## Notes

- Questo DL completa `DL-ARCH-V2-007` sul piano strutturale e `DL-ARCH-V2-008` sul piano runtime.
- Il contratto e volutamente minimale ma obbligatorio.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
