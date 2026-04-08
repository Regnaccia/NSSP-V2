# ODE V2 - Stato Progetto

## Date
2026-04-08

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha chiuso tre stream applicativi minimi:

- `logistica`
- `produzione/articoli`
- `produzioni`

Sono oggi disponibili:

- backend base, auth browser e surface `admin`
- sync reale Easy read-only per `clienti` e `destinazioni`
- Core slice `clienti + destinazioni`
- UI browser clienti/destinazioni
- sync on demand backend-controlled per la surface logistica
- sync reale Easy read-only per `articoli`
- Core `articoli`
- UI browser `articoli`
- sync on demand backend-controlled per `articoli`
- catalogo interno `famiglie articolo`
- associazione articolo -> famiglia
- filtro famiglia nella lista articoli
- vista dedicata al catalogo `famiglie articolo`
- gestione minima del catalogo famiglie
- flag `considera_in_produzione` nel catalogo famiglie
- mapping tecnico iniziale `produzioni` da Easy (`DPRE_PROD` / `SDPRE_PROD`)
- sync reale Easy read-only per `produzioni_attive` e `produzioni_storiche`
- Core `produzioni` con `bucket`, `stato_produzione` e `forza_completata`
- UI browser `produzioni` consultiva a `2 colonne`
- sync on demand backend-controlled per `produzioni`
- prima gestione operativa del flag `forza_completata`
- default lista `produzioni` su `active`, con storico esplicito
- filtri `stato_produzione` e ricerca per articolo/documento
- sync reale Easy read-only per `MAG_REALE`
- computed fact canonica `inventory_positions`
- giacenza esposta nel dettaglio UI `articoli`

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-018`
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

- `TASK-V2-001` -> `TASK-V2-041`

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
- `TASK-V2-024` filtro famiglia articoli
- `TASK-V2-025` UI tabella famiglia articoli
- `TASK-V2-026` gestione famiglie articoli
- `TASK-V2-027` flag considera in produzione famiglie
- `TASK-V2-028` sync produzioni attive
- `TASK-V2-029` sync produzioni storiche
- `TASK-V2-030` Core produzioni
- `TASK-V2-031` UI produzioni
- `TASK-V2-032` sync on demand produzioni
- `TASK-V2-033` gestione operativa `forza_completata`
- `TASK-V2-034` performance produzioni con default `active`
- `TASK-V2-035` filtri e ricerca produzioni
- `TASK-V2-036` sync `MAG_REALE`
- `TASK-V2-037` computed fact `inventory_positions`
- `TASK-V2-038` giacenza nel dettaglio `articoli`
- `TASK-V2-039` refresh sequenziale `articoli -> mag_reale -> inventory_positions`
- `TASK-V2-040` sync `righe_ordine_cliente`
- `TASK-V2-041` Core `ordini cliente`

## Task aperti

- `TASK-V2-042` `commitments` cliente
- `TASK-V2-043` `commitments` produzione

## Gap noti

- la documentazione `UIX` e separata tra pattern generale e spec caso concreto; i prossimi casi dovranno aggiungere nuove spec dedicate
- il catalogo `famiglie articolo` e ormai un vero riferimento interno; i prossimi stream dovranno decidere se riusare lo stesso pattern anche per altri cataloghi di dominio
- i report `docs/test/` coprono formalmente solo i primi test storici; per i task piu recenti la verifica vive nelle `Completion Notes`

## Prossima sequenza consigliata

Ordine pragmatico raccomandato:

1. completare il primo computed fact `commitments` cliente
2. estendere `commitments` alla provenienza `production`
3. usare `inventory` e `commitments` come building block per la futura `availability`

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
