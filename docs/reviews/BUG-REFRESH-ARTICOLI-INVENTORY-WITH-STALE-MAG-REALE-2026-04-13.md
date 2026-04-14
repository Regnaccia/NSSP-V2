# BUG: `refresh_articoli()` ricostruisce `inventory_positions` anche se `mag_reale` fallisce

**Data rilevazione**: 2026-04-13
**Rilevato da**: review tecnica progetto V2
**Severity**: Media - puo produrre un refresh quantitativo parzialmente "success" su dati di magazzino non aggiornati

---

## Sintomo

Nel refresh semantico della surface `articoli`, lo step di rebuild
`inventory_positions` viene eseguito sempre, anche quando la sync `mag_reale`
non e andata a buon fine.

Questo significa che la response del refresh puo mostrare:

- `mag_reale = error`
- `inventory_positions = success`

pur avendo ricostruito la giacenza su un mirror vecchio o parziale.

## Evidenza nel codice

In [refresh_articoli.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/refresh_articoli.py:169)
vengono letti solo due prerequisiti:

- `righe_ok`
- `produzioni_ok`

Subito dopo lo step inventory viene eseguito incondizionatamente:

- [refresh_articoli.py](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/backend/src/nssp_v2/app/services/refresh_articoli.py:174)

Non esiste un controllo equivalente a:

- `mag_reale_ok = sync_status.get("mag_reale") == "success"`

## Causa radice

La chain assume implicitamente che il rebuild di `inventory_positions` dipenda solo
dal fatto che il mirror `sync_mag_reale` esista, non dal fatto che lo step di sync
corrente sia riuscito.

Come tradeoff operativo puo avere un senso in alcuni scenari di "best effort", ma:

- il comportamento non e esplicitato come decisione architetturale
- nella response step-by-step puo sembrare che la catena quantitativa sia sana
  quando in realta ha riusato dati stantii

## Impatto

- feedback operativo ambiguo al chiamante
- rischio di considerare aggiornato `inventory_positions` quando non lo e
- maggiore difficolta nel debugging di refresh parziali
- possibile propagazione di dati non riallineati a `availability`
  se gli step successivi vengono sbloccati da prerequisiti non abbastanza stretti

## Distinzione dal bug noto `sync_mag_reale`

Questo bug non riguarda cancellazioni/rettifiche non gestite nel mirror.
Riguarda la logica di orchestrazione del refresh semantico:

- anche con strategia `mag_reale` invariata
- anche senza delete handling

lo step inventory dovrebbe avere una semantica chiara rispetto al fallimento del
prerequisito `mag_reale` nel run corrente.

## Direzione di risoluzione

Opzione conservativa consigliata:

1. introdurre `mag_reale_ok`
2. eseguire `_run_inventory_rebuild()` solo se `mag_reale_ok`
3. restituire `skipped` in caso contrario

Opzione alternativa, se si vuole mantenere il comportamento corrente:

- documentare esplicitamente che `inventory_positions` puo essere ricostruito su
  ultimo mirror valido disponibile
- differenziare lo status da `success` pieno, ad esempio con un motivo di
  `stale-input` o nota equivalente
