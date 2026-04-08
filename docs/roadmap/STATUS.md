# ODE V2 - Stato Progetto

## Date
2026-04-07

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha gia chiuso due stream applicativi minimi:

- `logistica`
- `produzione/articoli`

Sono oggi disponibili:

- backend base, auth browser e surface `admin`
- sync reale Easy read-only per `clienti` e `destinazioni`
- Core slice `clienti + destinazioni`
- UI browser iniziale della surface clienti/destinazioni
- trigger `sync on demand` backend-controlled per la surface logistica
- sync reale Easy read-only per `articoli`
- Core `articoli`
- UI browser `articoli`
- trigger `sync on demand` backend-controlled per `articoli`
- prima configurazione interna `famiglia articolo`

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-014`
- `UIX/` fino a `DL-UIX-V2-004`

Supporti attivi:

- `UIX/specs/` per i casi concreti che istanziano i pattern UIX

Punti ormai stabili:

- separazione `sync / core / app / shared`
- Easy solo read-only
- sync per entita con run metadata e freshness anchor
- Core come ponte tra mirror sync e surface applicative
- navigazione multi-surface con evoluzione verso navigazione contestuale

## Task completati

Completati:

- `TASK-V2-001` -> `TASK-V2-017`
- `TASK-V2-018`
- `TASK-V2-019`
- `TASK-V2-020`
- `TASK-V2-021`
- `TASK-V2-022`
- `TASK-V2-023`

In particolare il primo caso applicativo oggi copre:

- `TASK-V2-010` sync clienti reale
- `TASK-V2-011` sync destinazioni reale
- `TASK-V2-012` Core clienti/destinazioni
- `TASK-V2-013` UI clienti/destinazioni
- `TASK-V2-014` sync on demand backend-controlled
- `TASK-V2-015` integrazione della destinazione principale derivata
- `TASK-V2-016` refinement scroll indipendente delle colonne
- `TASK-V2-017` navigazione contestuale per-surface
- `TASK-V2-018` sync articoli reale
- `TASK-V2-019` Core articoli
- `TASK-V2-020` UI articoli
- `TASK-V2-021` sync on demand articoli
- `TASK-V2-022` famiglia articoli
- `TASK-V2-023` UI famiglia articoli

## Task aperti

Previsti come prossimi passi:

- `TASK-V2-024` filtro famiglia articoli
- `TASK-V2-025` UI tabella famiglia articoli
- `TASK-V2-026` gestione famiglie articoli
- `TASK-V2-027` flag considera in produzione famiglie

## Gap noti

- la documentazione `UIX` e ora separata tra pattern generale e spec caso concreto; i prossimi casi dovranno aggiungere nuove spec dedicate
- i prossimi stream dovranno decidere se riusare il pattern `mirror esterno + primo dato interno` oppure introdurre un dominio interno piu autonomo
- i report `docs/test/` coprono formalmente solo i primi test storici; per i task piu recenti la verifica vive nelle `Completion Notes`

## Prossima sequenza consigliata

Ordine pragmatico raccomandato:

1. definire il prossimo slice di dominio o di configurazione
2. `TASK-V2-024`
3. `TASK-V2-025`
4. `TASK-V2-026`
5. `TASK-V2-027`

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
