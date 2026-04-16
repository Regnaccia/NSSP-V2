# TASK-V2-132 - UI articoli proposal logic friendly labels and params template

## Status
Completed

## Date
2026-04-16

## Owner
Codex

## Source Documents

- `docs/task/TASK-V2-130-ui-admin-proposal-logic-two-column-governance.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`

## Goal

Rendere la configurazione della proposal logic nella schermata `articoli` piu guidata e leggibile:

- selezione della `proposal_logic_key` con label human-friendly
- precompilazione del JSON params con la shape minima attesa quando la logica richiede parametri obbligatori

## Context

La UI admin delle logiche proposal ha gia iniziato a introdurre:

- label leggibili
- descrizioni human-friendly

La schermata `articoli` pero continua a essere il punto in cui l'operatore assegna la logica al singolo articolo. Se qui restano visibili solo le key tecniche, la UX resta incoerente e piu fragile.

Questo e particolarmente rilevante ora che il catalogo delle logiche proposal sta crescendo:

- `proposal_target_pieces_v1`
- `proposal_full_bar_v1`
- `proposal_full_bar_v2_capacity_floor`
- `proposal_multi_bar_v1_capacity_floor`

Inoltre, quando una proposal logic richiede parametri articolo-specifici, l'operatore oggi deve ricordare:

- il nome esatto della chiave JSON
- la struttura minima attesa

Questo e fragile.

Primo caso atteso:

- se viene selezionata `proposal_multi_bar_v1_capacity_floor`
- il campo JSON deve potersi precompilare almeno come:

```json
{
  "bar_multiple": null
}
```

## Scope

- mostrare nel selettore proposal logic della schermata `articoli` le label human-friendly
- mantenere la key tecnica come valore persistito/trasmesso al backend
- riallineare il testo UI con lo stesso vocabolario usato in admin
- introdurre un template minimo dei `proposal_logic_article_params` in base alla logic selezionata
- precompilare il JSON params quando la logic cambia e il JSON corrente e vuoto o compatibile con il reset guidato
- supportare almeno il primo caso noto:
  - `proposal_multi_bar_v1_capacity_floor -> { "bar_multiple": null }`
- lasciare invariato il contratto backend di salvataggio

## Out of Scope

- redesign completo della schermata `articoli`
- cambio del modello backend proposal logic
- introduzione di descrizioni lunghe o drawer esplicativi in `articoli`
- validazione backend dei params
- editor form-based completo per tutti i params possibili

## Constraints

Regole minime:

- il backend continua a ricevere e salvare `proposal_logic_key`
- la UI mostra label leggibili nel `select`
- la key tecnica puo restare visibile come supporto secondario solo se utile, ma non come primary label
- la fonte delle label deve essere coerente con quella usata in admin, evitando duplicazioni semantiche divergenti
- la precompilazione del JSON deve essere guidata dalla logic selezionata
- il template e un aiuto UX, non sostituisce la validazione backend
- non vanno persi in modo silenzioso params gia valorizzati dall'utente
- la UI deve evitare reset distruttivi se il JSON contiene gia dati utili

Primo caso obbligatorio:

- `proposal_multi_bar_v1_capacity_floor`
  - template minimo:
    - `{ "bar_multiple": null }`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` Si
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 01 - Entita governata in admin, consumata nelle surface operative`
- `Pattern 04 - Core read model prima della UI`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La schermata `articoli` continua a usare il normale save della configurazione articolo.

## Acceptance Criteria

- il selettore proposal logic in `articoli` mostra label human-friendly
- il valore persistito resta la key tecnica
- la UI `articoli` usa lo stesso vocabolario di label della schermata admin proposal logic
- selezionando una logic che richiede params, il JSON mostra la shape minima attesa
- il primo caso supportato e `proposal_multi_bar_v1_capacity_floor`
- la UI non obbliga l'utente a ricordare il nome della chiave JSON
- la build frontend resta verde

## Deliverables

- refinement UI del selettore proposal logic in `articoli`
- refinement UI del campo `proposal_logic_article_params`
- eventuale helper/shared mapping per riuso di:
  - label logiche
  - template params minimi

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### `frontend/src/lib/proposalLogicMeta.ts` — NEW FILE

Fonte condivisa tra `AdminProposalLogicPage` e `ProduzioneHome`:

- `PROPOSAL_LOGIC_META`: mappa di 5 logiche → `{ label, description }`
- `proposalLogicMeta(logicKey)`: restituisce metadati o fallback con la key come label
- `PROPOSAL_LOGIC_ARTICLE_PARAMS_TEMPLATE`: template params minimi articolo-specifici per logica
- `proposalLogicParamsTemplate(logicKey)`: restituisce il template JSON serializzato o `null`

Primo template supportato:
- `proposal_multi_bar_v1_capacity_floor → { "bar_multiple": null }`

### `frontend/src/pages/surfaces/ProduzioneHome.tsx`

Import aggiunto:
```typescript
import { proposalLogicMeta, proposalLogicParamsTemplate } from '@/lib/proposalLogicMeta'
```

**Select proposal logic**:
- Le `<option>` ora mostrano `proposalLogicMeta(logicKey).label` (label human-friendly)
- La key tecnica resta il `value` persistito/trasmesso al backend
- Label "Logic key articolo" → "Logica proposal articolo"

**onChange con auto-populate params**:
```typescript
onChange={(e) => {
  const newKey = e.target.value
  setProposalLogicKeyInput(newKey)
  if (newKey) {
    const tpl = proposalLogicParamsTemplate(newKey)
    const currentIsEmpty = proposalLogicParamsInput.trim() === '{}' || proposalLogicParamsInput.trim() === ''
    if (tpl && currentIsEmpty) {
      setProposalLogicParamsInput(tpl)
    }
  }
}}
```

Regola non-distruttiva: il template viene applicato solo se il JSON corrente è vuoto o `{}`.
Se l'utente ha già valorizzato i params, non vengono sovrascritti.

### `frontend/src/pages/surfaces/AdminProposalLogicPage.tsx`

Rimossi `PROPOSAL_LOGIC_META` e `proposalLogicMeta` locali, sostituiti con import da `@/lib/proposalLogicMeta`.

**Esito build:** `✓ built in 7.80s`, exit code `0`.
