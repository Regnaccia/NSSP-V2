# TASK-V2-148 - Legacy compatibility review before code removal

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/roadmap/CLEANUP_PLAN_2026-04-17.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-043.md`

## Goal

Rivedere alias, route e compatibilita legacy ancora presenti nel codice prima di qualsiasi rimozione distruttiva.

## Scope

- censire alias proposal e riferimenti legacy ancora presenti
- distinguere:
  - compatibilita ancora necessarie
  - compatibilita rimovibili
- proporre il delta di cleanup codice successivo

## Out of Scope

- rimozione diretta del codice
- refactor funzionali non collegati
- modifiche ai dati persistiti

## Constraints

- ogni elemento legacy va verificato per:
  - riferimenti runtime
  - riferimenti UI
  - riferimenti test
  - impatto su dati/config esistenti

## Acceptance Criteria

- esiste una lista breve di compatibilita da mantenere
- esiste una lista breve di compatibilita candidate alla rimozione
- il progetto puo aprire task di code cleanup senza cancellazioni al buio

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-19

Review completa. Nessun codice rimosso. Output: lista compatibilità da mantenere e lista candidati alla rimozione.

---

### Cluster A — Criticita Articoli

#### Componenti censiti

| Elemento | File | Stato |
|----------|------|-------|
| Route UI | `frontend/src/App.tsx:190` | Esiste (`/produzione/criticita` → `CriticitaPage`) |
| Pagina UI | `frontend/src/pages/surfaces/CriticitaPage.tsx` | Esiste, con banner deprecazione |
| Tipo API | `frontend/src/types/api.ts` | `CriticitaItem` esiste |
| API endpoint | `backend/src/nssp_v2/app/api/produzione.py:379` | `GET /produzione/criticita` attivo |
| Core module | `backend/src/nssp_v2/core/criticita/` | `queries.py`, `logic.py`, `read_models.py`, `__init__.py` |
| Test suite | `backend/tests/core/test_core_criticita.py` | ~30 test attivi |

#### Impatto dati persistiti

Nessuno. Il modulo `criticita` non scrive dati nel DB interno: legge solo `CoreAvailability`, `SyncArticolo`, `CoreArticoloConfig`. La rimozione non richiede migration.

#### Classificazione

- **Da rimuovere in un task dedicato**: tutti e 6 gli elementi sopra, nell'ordine: route `App.tsx` → `CriticitaPage.tsx` → API endpoint → import in `produzione.py` → `core/criticita/` → test → tipo `CriticitaItem` da `types/api.ts`.
- **Prerequisito**: nessuno. La navigazione è già stata tolta (TASK-V2-147). La route è accessibile solo via URL diretto — accettabile come stato transitorio.

---

### Cluster B — Alias `proposal_required_qty_total_v1`

#### Componenti censiti

| Elemento | File | Dettaglio |
|----------|------|-----------|
| Registry backend | `core/production_proposals/config.py:14,23` | In `KNOWN_PROPOSAL_LOGICS` e `_DEFAULT_PARAMS_BY_KEY` |
| Logic backend | `core/production_proposals/logic.py:45,53` | Trattato come alias di `proposal_target_pieces_v1` |
| Metadata frontend | `frontend/src/lib/proposalLogicMeta.ts:19` | Voce con label "Pezzi a target (alias legacy)" |
| Display frontend | `frontend/src/pages/surfaces/ProductionProposalsPage.tsx:62` | Guard `if (logicKey === 'proposal_required_qty_total_v1') return 'Pezzi'` |
| Test backend | `backend/tests/core/test_core_proposal_logic_config.py:40,68,78` | 3 test che verificano l'alias |
| Doc storico | `docs/task/TASK-V2-117.md` | Contesto storico — non toccare |

#### Impatto dati persistiti

**Potenziale.** Il campo `proposal_logic_key` su `CoreArticoloConfig` è una stringa in DB. Se un articolo ha il valore `'proposal_required_qty_total_v1'` persistito, la rimozione dall'alias registry causerebbe:

- `resolve_article_proposal_logic` nel workspace proposal non riconoscerebbe più la chiave come valida
- l'articolo riceverebbe un fallback involontario a `proposal_target_pieces_v1` con `proposal_fallback_reason` valorizzato

La verifica dello stato DB non è stata eseguita in questo task (richiederebbe accesso al DB di produzione).

#### Classificazione

- **Da tenere per ora**: tutti i componenti sopra.
- **Rimovibile solo dopo**:
  1. Query DB: `SELECT DISTINCT proposal_logic_key FROM core_articolo_config WHERE proposal_logic_key = 'proposal_required_qty_total_v1'`
  2. Se presente: migration che sostituisce il valore con `'proposal_target_pieces_v1'`
  3. Poi rimozione coordinata di: `config.py` → `logic.py` → `proposalLogicMeta.ts` → guard in `ProductionProposalsPage.tsx` → test
- **Task suggerito**: aprire un task dedicato `TASK-V2-149` solo dopo la verifica DB.

---

### Riepilogo

#### Compatibilità da mantenere (per ora)

- `proposal_required_qty_total_v1`: alias runtime potenzialmente attivo su dati DB. Richiede verifica DB e migration prima di qualsiasi rimozione.

#### Compatibilità candidate alla rimozione (task dedicato)

- **Stack Criticita** (6 elementi): nessun impatto su dati persistiti. Task unico, sequenza precisa documentata sopra.
- **Alias `proposal_required_qty_total_v1`** (5 elementi): rimovibile solo dopo verifica DB + eventuale migration.

#### Task successivi suggeriti

- `TASK-V2-149`: verifica DB `proposal_logic_key` + migration se necessario + rimozione alias
- `TASK-V2-150` (o accorpato): rimozione completa stack Criticita
