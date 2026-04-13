# TASK-V2-070 - UI allineamento nomenclatura planning_mode

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/task/TASK-V2-069-allineamento-nomenclatura-planning-mode.md`

## Goal

Riallineare la UI gia coinvolta dal modello planning al nuovo vocabolario esplicito `planning_mode`, senza modificare ancora il comportamento funzionale delle surface.

## Context

`TASK-V2-069` copre il riallineamento di nomenclatura nei contratti, helper e read model.

Resta pero un secondo passaggio necessario:

- evitare che le schermate continuino a parlare solo tramite il booleano `aggrega_codice_in_produzione`
- usare in UI il vocabolario esplicito:
  - `planning_mode = by_article`
  - `planning_mode = by_customer_order_line`

Questo task e intenzionalmente distinto da `069` per non rallentare il passaggio gia in lavorazione sul Core/contratti.

## Scope

- riallineare label, testi di supporto, tooltip e naming UI gia coinvolti dal modello planning
- usare il vocabolario `planning_mode` dove la UI espone o spiega il comportamento di aggregazione
- mantenere il legame con la configurazione esistente:
  - `effective_aggrega_codice_in_produzione` resta il driver dati
  - `planning_mode` e la nomenclatura esplicita mostrata o usata nei contratti UI
- toccare solo le schermate gia coinvolte dal modello planning, in particolare:
  - `famiglie articolo`
  - dettaglio `articoli`
  - eventuale surface `Planning Candidates` se gia usa/mostra il concetto

## Out of Scope

- cambiare la logica Core di `Planning Candidates`
- introdurre gia il branch comportamentale `by_customer_order_line`
- modificare la persistenza o il modello dati delle policy
- introdurre nuove configurazioni indipendenti dal modello gia esistente

## Constraints

- il task e di UI/naming, non di behavior change
- i testi UI devono essere comprensibili anche a operatori non tecnici
- dove utile, il vocabolario utente puo essere piu descrittivo del nome tecnico, ma deve restare mappabile senza ambiguita a:
  - `by_article`
  - `by_customer_order_line`
- evitare regressioni nelle schermate gia funzionanti

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Se vengono toccate schermate con pulsante `Aggiorna`, il task non deve cambiare la funzione di refresh chiamata.
Il riallineamento e solo di nomenclatura e presentazione.

## Acceptance Criteria

- le schermate gia coinvolte dal modello planning non espongono piu il concetto solo come booleano opaco
- il vocabolario UI e coerente con:
  - `planning_mode = by_article`
  - `planning_mode = by_customer_order_line`
- nessun comportamento funzionale planning cambia ancora rispetto allo stato attuale
- la completion note elenca chiaramente quali schermate e quali testi/componenti sono stati riallineati

## Verification Level

- `Mirata`

Verifiche minime richieste:

- test frontend/backend mirati solo se necessari per componenti/contratti toccati
- `npm run build`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

Il riallineamento di roadmap, overview e guide trasversali viene fatto dopo da Codex.

## Contracts / Flows Changed

**FamigliePage.tsx** (`/produzione/famiglie`):
- Intestazione colonna: `"Aggrega codice"` → `"Planning mode"` con tooltip esplicito `by_article / by_customer_order_line`
- Checkbox `title` per ogni riga: `"Aggregata per codice"` / `"Non aggregata per codice"` → `"by_article — aggrega per codice articolo"` / `"by_customer_order_line — per riga ordine cliente"`
- Toast error toggle: `"Impossibile aggiornare il flag aggregazione"` → `"Impossibile aggiornare la modalità planning"`
- Commento header endpoint: aggiornato per menzionare `planning_mode` anziché `aggrega_codice_in_produzione`

**ProduzioneHome.tsx** — sezione `Planning policy` nel dettaglio articolo:
- Label select: `"Aggrega per codice in produzione"` → `"Modalità planning"`
- Opzioni select:
  - `"Sì — aggrega"` → `"by_article — aggrega per codice"`
  - `"No — non aggregare"` → `"by_customer_order_line — per riga ordine"`
- Valore effettivo: ora legge `detail.planning_mode` (stringa esplicita) invece di `effectiveLabel(effective_aggrega_codice_in_produzione)` (Sì/No); colorazione aggiornata su `planning_mode`

**PlanningCandidatesPage.tsx**: nessuna modifica — la surface non espone il concetto di aggregazione come testo visibile agli operatori.

Refresh non modificato in nessuna delle schermate toccate.

## Documentation Impact

Nessun impatto documentale trasversale — task puramente di UI/naming.

## Completion Notes

TASK-V2-070 completato. Build frontend pulita. Nessuna regressione.

Le schermate che esponevano il concetto di aggregazione solo come booleano opaco ora usano il vocabolario esplicito `by_article` / `by_customer_order_line` in label, tooltip e opzioni select. Il driver dati `effective_aggrega_codice_in_produzione` rimane invariato; la UI consuma `planning_mode` per la presentazione.

## Verification Notes

- `npm run build` — build TypeScript + Vite pulita, 0 errori, 0 warning

## Completed At

2026-04-10

## Completed By

Claude Code
