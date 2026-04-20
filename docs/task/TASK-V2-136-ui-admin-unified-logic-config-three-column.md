# TASK-V2-136 - UI Admin unified logic config a 3 colonne

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/SYSTEM_OVERVIEW.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-130-ui-admin-proposal-logic-two-column-governance.md`
- `docs/task/TASK-V2-090-admin-stock-logic-config.md`
- `docs/task/TASK-V2-095-admin-stock-logic-separate-page.md`

## Goal

Unificare la governance delle logiche operative in una singola pagina admin, denominata ad esempio `Logic Config`, con layout a `3 colonne`:

- colonna sinistra: dominio logico (`proposal`, `stock`, `capacity`, ... )
- colonna centrale: elenco logiche del dominio selezionato
- colonna destra: configurazione/dettaglio della logica selezionata

## Context

Oggi la governance delle logiche e cresciuta per slice:

- pagina admin stock logic
- pagina admin proposal logic

La direzione richiesta e consolidare queste superfici in una UI unica e piu scalabile, evitando proliferazione di pagine separate quando i domini logici aumentano.

La pagina unificata deve restare coerente con il rebase architetturale:

- moduli stabili
- confini chiari tra domini
- configurazione leggibile per operatori/admin

## Scope

- introdurre una nuova pagina admin unica per la governance logiche
- layout a `3 colonne`
- colonna sinistra con tipi di logica / domini
- colonna centrale con elenco logiche del dominio selezionato
- colonna destra con dettaglio e configurazione della logica selezionata
- consolidare almeno i domini gia attivi:
  - `proposal`
  - `stock`
  - `capacity` se gia semanticamente separato in UI, altrimenti preparare il contenitore

## Out of Scope

- redesign dei contratti backend delle logiche
- introduzione di nuove logiche di dominio
- cambiamenti al modello autorizzativo admin
- merge tecnico forzato dei backend stock/proposal se oggi restano distinti

## Constraints

Regole:

- la pagina unica deve essere di governance, non una dashboard operativa
- il dominio selezionato governa solo la colonna centrale/destra
- la pagina deve restare leggibile anche con crescita del catalogo logiche
- il vocabolario UI deve usare label e descrizioni human-friendly
- la persistenza backend puo restare distinta se il contratto corrente lo richiede

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` Si
- `Introduce configurazione che deve essere visibile in articoli?` Potenzialmente, per coerenza vocabolario
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 09 - Una surface per dominio, non per query locale`
- `Pattern 12 - Configurazione guidata e leggibile`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La pagina consuma configurazioni admin esistenti; non introduce catene di refresh.

## Acceptance Criteria

- esiste una pagina admin unica per la governance logiche
- il layout e a `3 colonne`
- colonna sinistra:
  - elenco domini logici
- colonna centrale:
  - elenco logiche del dominio selezionato
- colonna destra:
  - configurazione della logica selezionata
- proposal e stock risultano governabili da questa pagina unica
- label e descrizioni restano human-friendly

## Deliverables

- nuova/refinita pagina admin `Logic Config`
- eventuale riallineamento routing/navigation admin
- update docs correlate se necessarie

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
cd frontend
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### `frontend/src/pages/surfaces/AdminLogicConfigPage.tsx`

Nuova pagina unificata a 3 colonne:
- **Colonna sinistra (w-48)**: pulsanti dominio `Proposal` e `Stock` con label e descrizione
- **Colonna centrale (w-72)**: `ProposalCenter` (elenco logiche con badge Default/Disabilitata) o `StockCenter` (elenco strategy con badge Attiva) in base al dominio attivo
- **Colonna destra (flex-1)**: `ProposalDetail` (governance toggle/default/delete + params JSON) o `StockDetail` (attivazione + monthly params + capacity params fissi) in base al dominio attivo
- Entrambi i config vengono caricati al mount; il dominio governa solo colonna centrale/destra
- Confirm delete dialog proposal invariato rispetto ad `AdminProposalLogicPage`

### `frontend/src/App.tsx`

- Aggiunta route `/admin/logic-config` → `AdminLogicConfigPage` (roles: admin)

### `frontend/src/components/AppShell.tsx`

- Rimosse voci `Logiche stock` (`/admin/stock-logic`) e `Logiche proposal` (`/admin/proposal-logic`) dal sotto-menu admin
- Aggiunta voce `Logic Config` (`/admin/logic-config`)

**Esito build:** `✓ built in 3.47s`, exit code `0`.

