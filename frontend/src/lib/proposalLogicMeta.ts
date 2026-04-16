/**
 * Metadata human-friendly per le logiche proposal V1.
 *
 * Fonte unica condivisa tra AdminProposalLogicPage e ProduzioneHome (TASK-V2-132).
 * Usare questa mappa evita divergenze di label tra le due superfici.
 */

export type ProposalLogicMeta = {
  label: string
  description: string
}

export const PROPOSAL_LOGIC_META: Record<string, ProposalLogicMeta> = {
  proposal_target_pieces_v1: {
    label: 'Pezzi a target',
    description:
      'Propone esattamente il fabbisogno target del candidate. È la logica base e anche il fallback più semplice.',
  },
  proposal_required_qty_total_v1: {
    label: 'Pezzi a target (alias legacy)',
    description:
      'Alias legacy della logica a pezzi: propone esattamente il fabbisogno target del candidate.',
  },
  proposal_full_bar_v1: {
    label: 'Barra intera',
    description:
      'Lavora a barre intere del materiale grezzo. Arrotonda sempre in eccesso e, se sfora la capienza, ricade a pezzi.',
  },
  proposal_full_bar_v2_capacity_floor: {
    label: 'Barra intera con floor su capienza',
    description:
      'Prova prima la barra intera in eccesso; se sfora la capienza tenta una riduzione in difetto compatibile, altrimenti ricade a pezzi.',
  },
  proposal_multi_bar_v1_capacity_floor: {
    label: 'Multi-barra con floor su capienza',
    description:
      'Come "Barra intera con floor", ma moltiplica i pezzi per barra per un moltiplicatore articolo-specifico (bar_multiple). Richiede il parametro bar_multiple.',
  },
}

export function proposalLogicMeta(logicKey: string): ProposalLogicMeta {
  return (
    PROPOSAL_LOGIC_META[logicKey] ?? {
      label: logicKey,
      description: 'Nessuna descrizione disponibile.',
    }
  )
}

/**
 * Template minimo dei parametri articolo-specifici per ciascuna logica.
 *
 * Se la logica selezionata ha un template, viene proposto come precompilazione
 * quando il JSON corrente è vuoto o quando l'utente accetta esplicitamente il reset.
 * Se la logica non ha template, il campo rimane {} (nessun param atteso).
 */
export const PROPOSAL_LOGIC_ARTICLE_PARAMS_TEMPLATE: Record<string, Record<string, unknown>> = {
  proposal_multi_bar_v1_capacity_floor: { bar_multiple: null },
}

/**
 * Restituisce il template JSON già serializzato (pretty-printed) per la logica data,
 * o null se la logica non ha template.
 */
export function proposalLogicParamsTemplate(logicKey: string): string | null {
  const tpl = PROPOSAL_LOGIC_ARTICLE_PARAMS_TEMPLATE[logicKey]
  if (!tpl) return null
  return JSON.stringify(tpl, null, 2)
}
