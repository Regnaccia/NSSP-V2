/**
 * Metadata human-friendly e parametri template per le strategy di stock policy.
 *
 * Fonte unica condivisa tra AdminStockLogicPage e qualsiasi altro punto UI
 * che mostri le strategy di calcolo scorte.
 */

export type StockStrategyMeta = {
  label: string
  description: string
}

export const STOCK_STRATEGY_META: Record<string, StockStrategyMeta> = {
  monthly_stock_base_from_sales_v1: {
    label: 'Multi-finestra V1',
    description:
      'Stima il consumo mensile usando finestre di lookback multiple (default 12/6/3 mesi), ' +
      'filtro outlier z-score e percentile configurabile. Media semplice delle stime per finestra. ' +
      'Adatta ad articoli con domanda continua.',
  },
  monthly_stock_base_weighted_v2: {
    label: 'Multi-finestra pesata V2',
    description:
      'Come V1, ma usa una media pesata delle finestre al posto della media semplice: ' +
      'le finestre più recenti pesano di più (window_weights). ' +
      'Migliore per articoli con trend di crescita o calo in corso.',
  },
  monthly_stock_base_segmented_v1: {
    label: 'Segmentata V1',
    description:
      'Classifica ogni articolo per continuità della domanda (continuo / regolare / intermittente / dormante) ' +
      'e applica una formula diversa per segmento. ' +
      'Gli articoli continui usano il percentile con rilevamento trend; ' +
      'i regolari e intermittenti usano il throughput mensile evitando la distorsione da zero-fill. ' +
      'Adatta a cataloghi con molti articoli a rotazione bassa.',
  },
}

export function stockStrategyMeta(strategyKey: string): StockStrategyMeta {
  return (
    STOCK_STRATEGY_META[strategyKey] ?? {
      label: strategyKey,
      description: 'Nessuna descrizione disponibile.',
    }
  )
}

/**
 * Parametri di default per ogni strategy, usati come precompilazione
 * quando l'utente seleziona una strategy per la prima volta.
 */
export const STOCK_STRATEGY_PARAMS_DEFAULTS: Record<string, Record<string, unknown>> = {
  monthly_stock_base_from_sales_v1: {
    windows_months: [12, 6, 3],
    percentile: 70,
    zscore_threshold: 2.0,
    min_nonzero_months: 2,
    min_movements: 3,
  },
  monthly_stock_base_weighted_v2: {
    windows_months: [12, 6, 3],
    window_weights: [1, 2, 3],
    percentile: 70,
    zscore_threshold: 2.0,
    min_nonzero_months: 2,
    min_movements: 3,
  },
  monthly_stock_base_segmented_v1: {
    lookback_months: 12,
    continuous_threshold: 8,
    regular_threshold: 3,
    percentile_continuous: 70,
    zscore_threshold: 2.0,
    regular_factor: 1.2,
    intermittent_factor: 1.0,
    trend_ratio_threshold: 1.5,
    min_movements: 3,
  },
}

/**
 * Restituisce i parametri di default serializzati in JSON pretty-printed per la strategy data,
 * o null se la strategy non ha template.
 */
export function stockStrategyParamsTemplate(strategyKey: string): string | null {
  const tpl = STOCK_STRATEGY_PARAMS_DEFAULTS[strategyKey]
  if (!tpl) return null
  return JSON.stringify(tpl, null, 2)
}
