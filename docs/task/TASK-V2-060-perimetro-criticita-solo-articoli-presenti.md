# TASK-V2-060 - Perimetro criticita solo articoli presenti

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-024.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-055-criticita-articoli-v1.md`
- `docs/task/TASK-V2-056-refinement-ui-criticita-articoli.md`
- `docs/task/TASK-V2-058-refresh-criticita-collegato-a-refresh-articoli.md`
- `docs/task/TASK-V2-059-hardening-criticita-join-article-code.md`

## Goal

Rendere esplicito che la vista `criticita articoli` puo mostrare solo articoli presenti nella surface `articoli`, cioe presenti e attivi nel Core/read model `articoli`.

## Context

Oggi la vista `criticita` parte da `core_availability` e arricchisce il dato con `sync_articoli` tramite `outerjoin`.

Questo consente la comparsa di codici che:

- hanno una disponibilita negativa
- ma non sono visibili nella surface `articoli`

Il comportamento genera ambiguita operativa:

- l'utente vede in `criticita` un articolo che non riesce poi a trovare in `articoli`
- la criticita non e piu chiaramente ancorata alla stessa anagrafica consultiva usata nel resto della surface produzione

La regola voluta e piu stretta:

- la vista `criticita` deve essere un sottoinsieme operativo della surface `articoli`
- quindi puo mostrare solo articoli presenti nella lista `articoli`

## Scope

### In Scope

- limitare la vista `criticita` ai soli articoli presenti nel perimetro della surface `articoli`
- escludere dalla lista critica i codici orfani rispetto ad `articoli`
- allineare la query/read model `criticita` alla stessa anagrafica attiva usata dalla surface `articoli`
- aggiungere test di regressione espliciti sul caso:
  - disponibilita negativa
  - codice non presente o non attivo in `sync_articoli`
  - articolo escluso dalla vista `criticita`

### Out of Scope

- modifica della formula di criticita
- modifica della formula di `availability`
- redesign della vista UI
- modifica dei fact canonici gia materializzati

## Constraints

- la vista `criticita` resta basata su `availability` come fact sorgente
- il perimetro articoli deve pero essere esplicito e coerente con la surface `articoli`
- non introdurre deroghe implicite per articoli orfani
- la regola deve convivere con l'hardening raw/canonical di `TASK-V2-059`

## Refresh / Sync Behavior

La vista `criticita` deve riusare il refresh semantico backend della surface `articoli` (`refresh_articoli()`).

Questa regola e complementare a `TASK-V2-058`:

- `TASK-V2-058` collega il pulsante `Aggiorna` al refresh corretto
- questo task restringe il perimetro dati della lista critica agli articoli effettivamente presenti in `articoli`

Quindi, quando la vista `criticita` viene aggiornata, deve dipendere anche dal refresh della surface `articoli`.

## Acceptance Criteria

- la vista `criticita` mostra solo articoli presenti e attivi nella surface `articoli`
- un codice con `availability_qty < 0` ma assente da `articoli` non compare nella lista critica
- un codice con `availability_qty < 0` ma marcato non attivo in `sync_articoli` non compare nella lista critica
- esistono test di regressione mirati sul nuovo perimetro

## Deliverables

- hardening query/read model della vista `criticita`
- test di regressione dedicati
- completion notes con regola di perimetro resa esplicita

## Verification Level

`Mirata`

Questo task e un refinement del perimetro dati della vista `criticita`.

Quindi:

- test backend mirati sul slice `criticita`
- build frontend solo se cambia il contratto o la resa utente
- niente full suite obbligatoria

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- trattare `criticita` come proiezione operativa del dominio `articoli`, non come lista autonoma di soli fact negativi
- ancorare il perimetro alla stessa anagrafica attiva usata in `list_articoli`
- evitare `outerjoin` permissivi che reintroducono articoli orfani nella vista

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Regola di perimetro resa esplicita

La vista `criticita` è ora un **sottoinsieme operativo della surface `articoli`**: un codice
può comparire nella lista critica solo se è presente e attivo in `sync_articoli`.

Questo elimina la categoria di codici "orfani": codici con `availability_qty < 0` che
esistono in `core_availability` (perché il rebuild li ha elaborati in passato) ma che
non compaiono nella surface `articoli` — perché mai presenti o perché rimossi/disattivati.

Il comportamento precedente con `outerjoin` lasciava questi codici visibili in `criticita`,
creando ambiguità operativa: l'utente vedeva un articolo in `criticita` che non riusciva
a trovare in `articoli`.

### Modifiche backend

**`core/criticita/queries.py`** — una modifica strutturale alla query:

```python
# Prima (OUTERJOIN — codici orfani possibili):
.outerjoin(
    SyncArticolo,
    func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
)

# Dopo (INNER JOIN — solo articoli presenti e attivi in sync_articoli):
.join(
    SyncArticolo,
    func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
)
.filter(SyncArticolo.attivo == True)
```

Il filtro `SyncArticolo.attivo == True` era già presente nella query precedente come
`filter` su `outerjoin`, ma con `outerjoin` non produceva il risultato corretto: SQLAlchemy
applicava il filtro solo alle righe joinate, lasciando passare le righe NULL (orfane).
Con `join` (INNER JOIN) il filtro ha effetto pieno.

`func.upper()` sul lato raw è mantenuto da TASK-V2-059 per tollerare mismatch di casing.

### Test di regressione aggiunti

`tests/core/test_core_criticita.py` — 4 nuovi test sul perimetro TASK-V2-060:

- `test_perimetro_orfano_assente_da_sync_articoli` — codice con `availability_qty < 0`
  ma nessuna riga in `sync_articoli`: non compare nella lista critica.
- `test_perimetro_orfano_non_attivo_in_sync_articoli` — codice presente in `sync_articoli`
  ma con `attivo=False`: escluso dalla lista critica.
- `test_perimetro_articolo_attivo_incluso` — baseline positivo: codice attivo in `sync_articoli`
  e critico compare correttamente.
- `test_perimetro_misto_attivo_e_orfano` — due codici critici: uno attivo, uno orfano.
  Solo quello attivo compare nella lista.

Il file di test è stato interamente riscritto per adeguare tutti i test preesistenti
all'INNER JOIN: ogni test che prima si affidava all'assenza di `SyncArticolo` come
comportamento neutro ora aggiunge esplicitamente `_art()` quando l'articolo deve comparire.

Il test `test_list_criticita_v1_display_label_fallback_codice`, precedentemente basato
sull'assenza di `SyncArticolo` per il fallback, è stato adeguato: il fallback al codice
articolo si attiva ora con `_art(session, "ART001", None, None)` — descrizioni nulle,
non record mancante.

### Verifica

```
python -m pytest tests/core tests/app -q
298 passed in 6.55s
```

Frontend invariato — nessuna modifica al contratto API.

## Completed At

2026-04-10

## Completed By

Claude Code
