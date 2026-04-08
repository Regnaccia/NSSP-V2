# TASK-V2-024 - Filtro famiglia articoli

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-023-ui-famiglia-articoli.md`

## Goal

Introdurre nella surface `articoli` un filtro per `famiglia` che permetta di vedere:

- tutti gli articoli
- solo gli articoli non configurati
- solo gli articoli di una famiglia specifica

## Context

La surface `articoli` dispone gia di:

- lista articoli con ricerca
- dettaglio read-only dei dati Easy
- primo dato interno configurabile `famiglia articolo`

Il passo successivo naturale e rendere questa classificazione utile anche nella navigazione della lista, cosi da isolare rapidamente:

- articoli ancora da classificare
- articoli appartenenti a una famiglia specifica

Questo task e una rifinitura applicativa della surface esistente e non introduce un nuovo concetto architetturale.

## Scope

### In Scope

- filtro famiglia nella colonna sinistra della surface `articoli`
- opzione `Tutti`
- opzione `Non configurati`
- una opzione per ogni famiglia disponibile
- combinazione coerente tra:
  - filtro famiglia
  - ricerca articolo
- eventuale supporto backend al filtro se necessario per tenere il contratto pulito
- aggiornamento minimo della spec UIX articoli se il comportamento cambia in modo rilevante

### Out of Scope

- nuovi dati interni articolo
- CRUD del catalogo famiglie
- filtri multipli aggiuntivi
- sorting avanzato
- sync on demand

## Constraints

- il caso `Non configurati` deve essere esplicito e facilmente accessibile
- la ricerca articolo deve continuare a funzionare dentro il subset filtrato
- la surface deve restare coerente col pattern a `2 colonne`
- il task non deve introdurre un nuovo `DL`: e una rifinitura UI/Core del comportamento gia esistente

## Acceptance Criteria

- la UI espone un filtro famiglia nella lista articoli
- il filtro consente almeno:
  - `Tutti`
  - `Non configurati`
  - ogni famiglia disponibile
- la lista articoli si aggiorna correttamente in base al filtro selezionato
- la ricerca articolo continua a funzionare insieme al filtro
- `npm run build` passa senza errori

## Deliverables

- aggiornamento UI della surface `articoli`
- eventuale adeguamento backend/Core se necessario al filtro
- eventuali test frontend o backend coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
docker compose -f ../infra/docker/docker-compose.db.yml up -d
cp .env.example .env
alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
```

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il filtro visivamente vicino al campo ricerca
- usare una semantica chiara per il caso `Non configurati`
- evitare di introdurre logica duplicata frontend/backend se il contratto puo restare semplice
- se il dataset cresce, preferire un contratto backend esplicito piuttosto che affidarsi solo a filtro client-side

---

## Completion Notes

### Summary

Introdotto il filtro famiglia nella colonna lista articoli. Il filtro è client-side (nessuna modifica
al contratto Core/API — `famiglia_code` era già in `ArticoloItem` dal TASK-V2-022). Il tipo
`FamilyFilter = 'all' | 'unconfigured' | string` gestisce i tre casi. Il filtro si combina
con la ricerca: prima si applica il filtro famiglia, poi la ricerca testuale. Il contatore
risultati viene mostrato quando almeno uno dei due filtri è attivo.

### Files Changed

- `src/pages/surfaces/ProduzioneHome.tsx`:
  - tipo `FamilyFilter` e helper `matchesFamilyFilter`
  - `ColonnaArticoli` — nuovi prop `familyFilter`, `onFamilyFilterChange`, `famiglie`; `select` filtro famiglia sotto il campo ricerca; logica doppio filtro; contatore condizionale
  - `ProduzioneHome` — stato `familyFilter` inizializzato a `'all'`; props passati a `ColonnaArticoli`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md` — documentata sezione filtro famiglia nella colonna sinistra

### Dependencies Introduced

Nessuna.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code | Windows / Node | verde, 96 moduli, 273 kB JS |
| `python -m pytest tests -q` | Claude Code | Windows / .venv | 244 passed (backend invariato) |

### Assumptions

- Il filtro è interamente client-side perché `famiglia_code` è già incluso in ogni `ArticoloItem`.
  Se il dataset cresce molto (es. > 10k articoli), si potrebbe spostare il filtro al backend,
  ma per l'uso attuale non è necessario.
- Il reset del `familyFilter` al cambio articolo non è necessario — il filtro è sulla lista,
  non sul dettaglio.

### Known Limits

- Quando si imposta un filtro famiglia e poi si seleziona un articolo che poi viene classificato
  in una famiglia diversa, l'articolo può "sparire" dalla lista filtrata senza feedback esplicito.
  Accettabile per il primo slice.

### Follow-ups

- Evidenza visiva della famiglia assegnata nella riga lista (badge/label) per rendere il filtro
  più intuitivo da usare.

## Completed At

2026-04-07

## Completed By

Claude Code
