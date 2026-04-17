/**
 * Surface Admin — configurazione logiche stock (TASK-V2-095).
 *
 * Layout a 2 colonne identico ad AdminProposalLogicPage:
 * - sinistra: elenco strategy con badge attiva/inattiva
 * - destra: dettaglio strategy selezionata — descrizione, azione "Imposta come attiva",
 *           textarea JSON parametri monthly_base, sezione capacity params separata
 *
 * Contratto:
 * - una sola strategy e attiva alla volta (monthly_base_strategy_key)
 * - i parametri sono il JSON grezzo salvato in core_stock_logic_config.monthly_base_params_json
 * - la logica capacity e fissa (capacity_from_containers_v1), solo i suoi parametri sono editabili
 *
 * Consuma:
 *   GET /api/admin/stock-logic/config  — configurazione attiva + registry strategy
 *   PUT /api/admin/stock-logic/config  — aggiorna strategy, params monthly, params capacity
 */

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import { stockStrategyMeta, stockStrategyParamsTemplate } from '@/lib/stockLogicMeta'

// ─── Tipi ─────────────────────────────────────────────────────────────────────

interface StockLogicConfigResponse {
  monthly_base_strategy_key: string
  monthly_base_params: Record<string, unknown>
  capacity_logic_key: string
  capacity_logic_params: Record<string, unknown>
  is_default: boolean
  updated_at: string | null
  known_strategies: string[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

// ─── Componente principale ────────────────────────────────────────────────────

export default function AdminStockLogicPage() {
  const [config, setConfig] = useState<StockLogicConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Stato editing
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [monthlyParamsJson, setMonthlyParamsJson] = useState('{}')
  const [capacityParamsJson, setCapacityParamsJson] = useState('{}')
  const [activeKey, setActiveKey] = useState('')

  useEffect(() => {
    setLoading(true)
    apiClient
      .get<StockLogicConfigResponse>('/admin/stock-logic/config')
      .then((r) => applyConfig(r.data))
      .catch(() => toast.error('Impossibile caricare la configurazione logiche stock'))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function applyConfig(data: StockLogicConfigResponse) {
    setConfig(data)
    setActiveKey(data.monthly_base_strategy_key)
    setCapacityParamsJson(JSON.stringify(data.capacity_logic_params, null, 2))
    const key = selectedKey && data.known_strategies.includes(selectedKey)
      ? selectedKey
      : data.monthly_base_strategy_key
    setSelectedKey(key)
    setMonthlyParamsJson(
      key === data.monthly_base_strategy_key
        ? JSON.stringify(data.monthly_base_params, null, 2)
        : (stockStrategyParamsTemplate(key) ?? '{}')
    )
  }

  // Aggiorna params editor quando cambia la strategy selezionata
  useEffect(() => {
    if (!config || !selectedKey) return
    if (selectedKey === config.monthly_base_strategy_key) {
      setMonthlyParamsJson(JSON.stringify(config.monthly_base_params, null, 2))
    } else {
      // Precompila con i default della strategy
      setMonthlyParamsJson(stockStrategyParamsTemplate(selectedKey) ?? '{}')
    }
  }, [selectedKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectedMeta = useMemo(
    () => (selectedKey ? stockStrategyMeta(selectedKey) : null),
    [selectedKey],
  )

  const selectedIsActive = selectedKey === activeKey

  async function saveConfig(overrides: { newStrategyKey?: string } = {}) {
    if (!config || !selectedKey) return

    let parsedMonthly: Record<string, unknown>
    let parsedCapacity: Record<string, unknown>
    try {
      parsedMonthly = JSON.parse(monthlyParamsJson || '{}') as Record<string, unknown>
    } catch {
      toast.error('Parametri monthly base: JSON non valido')
      return
    }
    try {
      parsedCapacity = JSON.parse(capacityParamsJson || '{}') as Record<string, unknown>
    } catch {
      toast.error('Parametri capacity: JSON non valido')
      return
    }

    const strategyKey = overrides.newStrategyKey ?? activeKey

    setSaving(true)
    try {
      const { data } = await apiClient.put<StockLogicConfigResponse>('/admin/stock-logic/config', {
        monthly_base_strategy_key: strategyKey,
        monthly_base_params: parsedMonthly,
        capacity_logic_params: parsedCapacity,
      })
      applyConfig(data)
      toast.success('Configurazione salvata')
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setSaving(false)
    }
  }

  function handleSetActive() {
    if (!selectedKey || selectedIsActive) return
    setActiveKey(selectedKey)
    void saveConfig({ newStrategyKey: selectedKey })
  }

  function handleSaveParams(e: React.FormEvent) {
    e.preventDefault()
    void saveConfig()
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b shrink-0">
          <h1 className="text-base font-semibold">Logiche stock</h1>
        </div>
        <div className="flex items-center justify-center flex-1 text-sm text-muted-foreground">
          Caricamento...
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b shrink-0">
        <h1 className="text-base font-semibold">Logiche stock</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Strategy di calcolo base mensile e parametri della logica capacity.
          Una sola strategy è attiva alla volta.
        </p>
      </div>

      {/* Layout 2 colonne */}
      <div className="flex flex-1 overflow-hidden">

        {/* Colonna sinistra — elenco strategy */}
        <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b bg-muted/30">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Strategy disponibili
            </span>
          </div>
          <div className="flex-1 overflow-y-auto divide-y">
            {(config?.known_strategies ?? []).map((key) => {
              const meta = stockStrategyMeta(key)
              const isActive = key === activeKey
              const isSelected = key === selectedKey

              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedKey(key)}
                  className={`w-full text-left px-4 py-3 flex flex-col gap-0.5 transition-colors ${
                    isSelected
                      ? 'bg-foreground/5 border-l-2 border-l-foreground'
                      : 'hover:bg-muted/40 border-l-2 border-l-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium">{meta.label}</span>
                    {isActive && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                        Attiva
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-muted-foreground/70">{key}</span>
                </button>
              )
            })}
          </div>

          {config?.updated_at && (
            <div className="px-4 py-2 border-t bg-muted/20 text-[11px] text-muted-foreground">
              Aggiornato: {new Date(config.updated_at).toLocaleString('it-IT')}
            </div>
          )}
        </div>

        {/* Colonna destra — dettaglio strategy selezionata */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedKey || !selectedMeta ? (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              Seleziona una strategy dalla lista.
            </div>
          ) : (
            <div className="max-w-2xl space-y-6">

              {/* Intestazione strategy */}
              <div className="space-y-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-base font-semibold">{selectedMeta.label}</h2>
                  {selectedIsActive && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                      Attiva
                    </span>
                  )}
                  {config?.is_default && selectedIsActive && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                      Default di sistema
                    </span>
                  )}
                </div>
                <p className="text-xs font-mono text-muted-foreground">Key: {selectedKey}</p>
                <p className="text-sm text-muted-foreground mt-1">{selectedMeta.description}</p>
              </div>

              {/* Azione attivazione */}
              {!selectedIsActive && (
                <div className="border rounded-lg p-4 bg-muted/20">
                  <h3 className="text-sm font-semibold mb-2">Attivazione</h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    Impostando questa strategy come attiva, il sistema userà i parametri
                    qui configurati per calcolare <code className="font-mono">monthly_stock_base_qty</code> di tutti gli articoli.
                  </p>
                  <button
                    type="button"
                    onClick={handleSetActive}
                    disabled={saving}
                    className="py-1.5 px-3 rounded-md text-sm font-medium border hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors disabled:opacity-50"
                  >
                    Imposta come strategy attiva
                  </button>
                </div>
              )}

              {/* Parametri monthly base */}
              <form onSubmit={handleSaveParams} className="space-y-3 border rounded-lg p-4">
                <div>
                  <h3 className="text-sm font-semibold">Parametri monthly base</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    JSON salvato in <code className="font-mono">monthly_base_params_json</code>.
                    {!selectedIsActive && (
                      <span className="ml-1 text-amber-600">
                        Salvando si imposta anche questa strategy come attiva.
                      </span>
                    )}
                  </p>
                </div>
                <textarea
                  value={monthlyParamsJson}
                  onChange={(e) => setMonthlyParamsJson(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-52"
                  disabled={saving}
                  spellCheck={false}
                />
                <button
                  type="submit"
                  disabled={saving}
                  className="py-1.5 px-4 bg-foreground text-background rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {saving ? 'Salvataggio...' : 'Salva parametri'}
                </button>
              </form>

              {/* Parametri capacity — sempre visibili, indipendenti dalla strategy */}
              <div className="border rounded-lg p-4 space-y-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold">Parametri capacity</h3>
                    <span className="text-xs font-mono bg-secondary px-2 py-0.5 rounded">
                      {config?.capacity_logic_key ?? 'capacity_from_containers_v1'}
                    </span>
                    <span className="text-xs text-muted-foreground">(logica fissa)</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Formula: <code className="font-mono">capacity = max_container_weight_kg × contenitori / (peso_grammi / 1000)</code>.
                    Salvato in <code className="font-mono">capacity_logic_params_json</code>.
                  </p>
                </div>
                <textarea
                  value={capacityParamsJson}
                  onChange={(e) => setCapacityParamsJson(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-24"
                  disabled={saving}
                  spellCheck={false}
                />
                <button
                  type="button"
                  onClick={() => void saveConfig()}
                  disabled={saving}
                  className="py-1.5 px-4 bg-foreground text-background rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {saving ? 'Salvataggio...' : 'Salva parametri capacity'}
                </button>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  )
}
