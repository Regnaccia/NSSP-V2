# BUG: sync_mag_reale — movimenti eliminati in Easy restano nel mirror ODE

**Data rilevazione**: 2026-04-10
**Rilevato da**: analisi disponibilità articolo `18X11X125R`
**Severity**: Alta — produce disponibilità errate visibili nella UI e nei Planning Candidates

---

## Sintomo

L'articolo `18X11X125R` mostra in ODE disponibilità negativa (`-175`) mentre Easy
riporta disponibilità positiva (`+25`).

## Indagine

Confronto diretto tra mirror ODE e Easy (query su MAG_REALE via pyodbc):

| | QTA_CAR | QTA_SCA | Netto |
|---|---|---|---|
| **Easy** (fonte) | 16.582 | 16.557 | **+25** |
| **ODE mirror** | 16.582 | **16.757** | **-175** |

I **carichi concordano** (QTA_CAR identici). Il problema è negli **scarichi**: ODE
ha 200 unità in più di QTA_SCA rispetto a Easy.

Conteggio righe totale in MAG_REALE:

| | Righe |
|---|---|
| Easy | 337.917 |
| ODE mirror | **337.944** |

ODE ha **27 righe in più** rispetto a Easy. Queste righe sono movimenti che Easy ha
eliminato o rettificato dopo che ODE li aveva già acquisiti nel mirror.

**Non si tratta di dati mancanti storici**: Easy stesso per `18X11X125R` non ha
movimenti con ID < 218918. Il primo movimento in Easy per questo articolo parte da
ID 219329. Il mirror ODE è allineato sulla finestra storica corretta.

## Causa radice

La sync unit `mag_reale` dichiara esplicitamente:

```python
DELETE_HANDLING = "no_delete_handling"
```

La strategia è **append-only con cursor**: ODE acquisisce solo i movimenti con
`ID_MAGREALE > max(id_movimento)` già presente. I record già importati **non vengono
mai aggiornati né eliminati**, anche se Easy li cancella o rettifica.

Quando un operatore corregge un errore di magazzino in Easy (cancellazione o
rettifica di un movimento), il mirror ODE conserva il dato errato originale in
perpetuo, producendo una divergenza crescente sulla giacenza.

## Impatto

- `core_inventory_positions.on_hand_qty` è calcolato su `sync_mag_reale` — eredita
  la divergenza.
- `core_availability.availability_qty` = `on_hand - set_aside - committed` —
  sottrae da una base già errata.
- La surface **Criticità Articoli** e i **Planning Candidates** consumano
  `availability_qty` — mostrano shortage fittizi per gli articoli affetti.
- Qualsiasi articolo con movimenti rettificati/cancellati in Easy dopo il sync è
  potenzialmente affetto.

## Articoli noti affetti

- `18X11X125R`: −200 unità di scarico fantasma (disponibilità reale +25, ODE mostra −175)

## Soluzioni

### Fix puntuale (breve termine) — TASK-V2-073

Re-bootstrap completo di `sync_mag_reale`:

1. Truncate `sync_mag_reale` (resetta il mirror)
2. Re-sync da cursor=0 (`WHERE ID_MAGREALE > 0` = tutti i movimenti Easy)
3. Rebuild `core_inventory_positions`
4. Rebuild `core_availability`

Questo riporta il mirror ad un allineamento perfetto con Easy al momento
dell'esecuzione. La finestra di indisponibilità dati è il tempo del re-import
(~337K righe — stimato sotto 1 minuto via script).

**Limitazione residua**: dopo il re-bootstrap il problema si ripresenterà
progressivamente ogni volta che Easy elimina o rettifica movimenti già importati.
Il fix puntuale è una correzione, non una soluzione strutturale.

### Fix architetturale (lungo termine)

Aggiungere alla sync `mag_reale` una strategia di **reconciliazione periodica**:

- periodicamente (o on-demand) eseguire un confronto tra gli ID presenti nel mirror
  e gli ID attualmente presenti in Easy
- eliminare dal mirror i record che Easy ha cancellato
- aggiornare i record che Easy ha rettificato (cambiamento di QTA_CAR/QTA_SCA su
  un ID esistente)

Questa modifica cambia la strategia da `append_only` a `full_replace` (o
`reconcile`) — richiede una decisione architetturale esplicita (DL-ARCH).

## Script di diagnosi disponibile

`V2/backend/scripts/inspect_availability.py` — mostra il breakdown completo di
disponibilità per un singolo articolo: giacenza, set_aside, commitments per riga,
confronto con Easy.

Uso:
```
cd backend
.venv\Scripts\activate
python scripts/inspect_availability.py <CODICE_ARTICOLO>
```
