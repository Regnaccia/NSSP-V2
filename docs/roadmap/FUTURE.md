# FUTURE — Sviluppi confermati, non ancora implementati

Questo documento raccoglie decisioni prese e validate che attendono implementazione.
Le motivazioni dettagliate verranno promosse in futuri documenti V2 man mano che i concetti verranno chiariti.

---

## F1 — `famiglia` e `release_mode` su `articoli`

**Priorità:** alta — prerequisito per F2 e F3.

**Problema attuale:**
La distinzione tra articoli aggregati (standard) e articoli per-riga-ordine (speciali, barre, BCL)
è implementata tramite CASE SQL in `get_righe_da_processare` e dispatch nel router.
Aggiungere un nuovo tipo richiede modifiche in più punti con rischio di regressioni.

**Soluzione:**
```sql
ALTER TABLE articoli ADD COLUMN famiglia     varchar(20) DEFAULT NULL;
-- 'standard' | 'speciali' | 'barre' | 'bcl'

ALTER TABLE articoli ADD COLUMN release_mode varchar(20) DEFAULT 'aggregate';
-- 'aggregate': una riga per articolo
-- 'per_row':   una riga per riga ordine
```

- La migrazione popola i default da `categorie_articolo.famiglia` e dalla regola codice `S*`
- Tutta la logica di dispatch diventa un check su `release_mode`
- Il campo è configurabile direttamente in UI "Parametri articoli"

**Impatto:** 1 migrazione, refactor ~50 righe backend, aggiornamento UI parametri articoli.

---

## F2 — Sync on-demand non bloccante

**Priorità:** alta — problema operativo immediato.

**Problema attuale:**
Il sync periodico (ogni 5/60 minuti) introduce finestre di staleness significative.
Le decisioni su F1a/F1b vengono prese su dati potenzialmente obsoleti.

**Soluzione:**
- Ogni endpoint operativo (F1a, F1b) lancia sync delle dipendenze in background al primo accesso
- Risponde immediatamente con i dati correnti
- Il frontend mostra indicatore "aggiornamento in corso"
- Dopo 3-5s il frontend fa un secondo fetch automatico
- Il sync periodico resta come fallback

**Dipendenze:** nessuna — indipendente da F1.
**Impatto:** ~20 righe backend, ~5 frontend. Non tocca il modello dati.

---

## F3 — `pending_overrides` — persistenza override utente

**Priorità:** media.

**Problema attuale:**
Gli override utente (qty, sorgente, tipo produzione) sono mantenuti in React state.
Un refresh o una sessione scaduta cancella tutto il lavoro non ancora lanciato.

**Soluzione:**
```sql
CREATE TABLE pending_overrides (
  id              uuid PRIMARY KEY,
  articolo_id     uuid NOT NULL,
  riga_ordine_id  uuid,
  qty             integer,
  sorgente_json   jsonb,
  created_by      varchar(50),
  created_at      timestamptz,
  expires_at      timestamptz
);
```

- Override confermati nel modal → `PATCH /api/pending-overrides`
- `genera-commesse` legge prima da `pending_overrides`, poi fallback ai valori calcolati
- Pulizia automatica al lancio o a fine giornata
- `needs_review = true` quando sync aggiorna i facts e la qty diverge >10% dall'override

**Dipendenze:** F1 (usa `articolo_id` + `release_mode`).
**Impatto:** 1 tabella, 2 endpoint, cambio `LancioModal.tsx`.

---

## F4 — Completare modulo logistica

**Priorità:** alta.

**Stato attuale:** router e modello dati base presenti, flusso operativo incompleto.

**Da completare:** (da dettagliare in sessione dedicata)

---

## F5 — Completare modulo magazzino

**Priorità:** alta.

**Stato attuale:** kiosk base presente, flusso approntamento parziale.

**Da completare:** (da dettagliare in sessione dedicata)

---

## Ordine di esecuzione raccomandato

```
F1 — famiglia + release_mode  (prerequisito)
F2 — sync on-demand           (fix urgente, indipendente)
F3 — pending_overrides        (dopo F1)
F4 — logistica                (indipendente da F1-F3)
F5 — magazzino                (indipendente da F1-F3)
```

Dopo F4+F5: planning/release layer (vedi `POSSIBLE.md`).
