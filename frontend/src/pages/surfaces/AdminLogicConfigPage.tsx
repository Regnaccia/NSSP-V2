/**
 * Surface Admin — Logic Config unificata (TASK-V2-136).
 *
 * Layout a 3 colonne:
 * - sinistra (w-48):  selezione dominio logico (proposal, stock)
 * - centrale (w-72):  elenco logiche del dominio selezionato
 * - destra (flex-1):  configurazione/dettaglio della logica selezionata
 *
 * Consolida AdminProposalLogicPage e AdminStockLogicPage in una singola
 * superficie admin scalabile. I contratti backend restano distinti.
 *
 * Consuma:
 *   GET/PUT /api/admin/proposal-logic/config
 *   GET/PUT /api/admin/stock-logic/config
 */

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { ProposalLogicConfigResponse } from '@/types/api'
import { proposalLogicMeta } from '@/lib/proposalLogicMeta'
import { stockStrategyMeta, stockStrategyParamsTemplate } from '@/lib/stockLogicMeta'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type Domain = 'proposal' | 'stock'

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

// ─── Sezione Proposal ─────────────────────────────────────────────────────────

interface ProposalPanelProps {
  config: ProposalLogicConfigResponse
  selectedKey: string | null
  onSelectKey: (key: string) => void
  paramsJson: string
  onParamsChange: (v: string) => void
  defaultLogicKey: string
  disabledKeys: string[]
  saving: boolean
  onToggleEnabled: () => void
  onSetDefault: () => void
  onDeleteRequest: () => void
  onSaveParams: (e: React.FormEvent) => void
}

function ProposalCenter({ config, selectedKey, onSelectKey, defaultLogicKey, disabledKeys }: Pick<ProposalPanelProps, 'config' | 'selectedKey' | 'onSelectKey' | 'defaultLogicKey' | 'disabledKeys'>) {
  return (
    <>
      <div className="px-4 py-3 border-b bg-muted/30">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Logiche disponibili
        </span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y">
        {config.known_logics.map((key) => {
          const meta = proposalLogicMeta(key)
          const enabled = !disabledKeys.includes(key)
          const isDefault = key === defaultLogicKey
          const isSelected = key === selectedKey
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelectKey(key)}
              className={`w-full text-left px-4 py-3 flex flex-col gap-0.5 transition-colors ${
                isSelected
                  ? 'bg-foreground/5 border-l-2 border-l-foreground'
                  : 'hover:bg-muted/40 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`text-sm font-medium ${!enabled ? 'text-muted-foreground/60' : ''}`}>
                  {meta.label}
                </span>
                {isDefault && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                    Default
                  </span>
                )}
                {!enabled && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-50 text-red-700 border border-red-200">
                    Disabilitata
                  </span>
                )}
              </div>
              <span className="text-[11px] font-mono text-muted-foreground/70">{key}</span>
            </button>
          )
        })}
      </div>
      {config.updated_at && (
        <div className="px-4 py-2 border-t bg-muted/20 text-[11px] text-muted-foreground">
          Aggiornato: {new Date(config.updated_at).toLocaleString('it-IT')}
        </div>
      )}
    </>
  )
}

function ProposalDetail({
  config,
  selectedKey,
  paramsJson,
  onParamsChange,
  defaultLogicKey,
  disabledKeys,
  saving,
  onToggleEnabled,
  onSetDefault,
  onDeleteRequest,
  onSaveParams,
}: Omit<ProposalPanelProps, 'onSelectKey'>) {
  const meta = useMemo(() => (selectedKey ? proposalLogicMeta(selectedKey) : null), [selectedKey])
  if (!selectedKey || !meta) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Seleziona una logica dalla lista.
      </div>
    )
  }
  const isEnabled = !disabledKeys.includes(selectedKey)
  const isDefault = selectedKey === defaultLogicKey

  return (
    <div className="max-w-2xl space-y-6">
      {/* Intestazione */}
      <div className="space-y-1">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-base font-semibold">{meta.label}</h2>
          {isDefault && (
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
              Default globale
            </span>
          )}
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            isEnabled
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {isEnabled ? 'Abilitata' : 'Disabilitata'}
          </span>
        </div>
        <p className="text-xs font-mono text-muted-foreground">Key: {selectedKey}</p>
        <p className="text-sm text-muted-foreground mt-1">{meta.description}</p>
      </div>

      {/* Governance */}
      <div className="border rounded-lg p-4 space-y-3 bg-muted/20">
        <h3 className="text-sm font-semibold">Governance</h3>
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={onToggleEnabled}
            disabled={saving || isDefault}
            title={isDefault ? 'La logica di default non può essere disabilitata' : ''}
            className={`py-1.5 px-3 rounded-md text-sm font-medium border transition-colors disabled:opacity-50 ${
              isEnabled
                ? 'hover:bg-red-50 hover:text-red-700 hover:border-red-200'
                : 'hover:bg-green-50 hover:text-green-700 hover:border-green-200'
            }`}
          >
            {isEnabled ? 'Disabilita logica' : 'Riabilita logica'}
          </button>

          {!isDefault && isEnabled && (
            <button
              type="button"
              onClick={onSetDefault}
              disabled={saving}
              className="py-1.5 px-3 rounded-md text-sm font-medium border hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors disabled:opacity-50"
            >
              Imposta come default
            </button>
          )}

          {!isDefault && isEnabled && (
            <button
              type="button"
              onClick={onDeleteRequest}
              disabled={saving}
              className="py-1.5 px-3 rounded-md text-sm font-medium border border-red-200 text-red-700 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              Rimuovi dal catalogo articoli
            </button>
          )}
        </div>
        {isDefault && (
          <p className="text-xs text-muted-foreground">
            La logica di default non può essere disabilitata o rimossa.
            Per rimuoverla, prima imposta un'altra logica come default.
          </p>
        )}
      </div>

      {/* Parametri globali */}
      <form onSubmit={onSaveParams} className="space-y-3 border rounded-lg p-4">
        <h3 className="text-sm font-semibold">Parametri globali</h3>
        <textarea
          value={paramsJson}
          onChange={(e) => onParamsChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-40"
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
    </div>
  )
}

// ─── Sezione Stock ────────────────────────────────────────────────────────────

function StockCenter({ config, selectedKey, onSelectKey, activeKey }: {
  config: StockLogicConfigResponse
  selectedKey: string | null
  onSelectKey: (key: string) => void
  activeKey: string
}) {
  return (
    <>
      <div className="px-4 py-3 border-b bg-muted/30">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Strategy disponibili
        </span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y">
        {config.known_strategies.map((key) => {
          const meta = stockStrategyMeta(key)
          const isActive = key === activeKey
          const isSelected = key === selectedKey
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelectKey(key)}
              className={`w-full text-left px-4 py-3 flex flex-col gap-0.5 transition-colors ${
                isSelected
                  ? 'bg-foreground/5 border-l-2 border-l-foreground'
                  : 'hover:bg-muted/40 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex items-center gap-1.5 flex-wrap">
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
      {config.updated_at && (
        <div className="px-4 py-2 border-t bg-muted/20 text-[11px] text-muted-foreground">
          Aggiornato: {new Date(config.updated_at).toLocaleString('it-IT')}
        </div>
      )}
    </>
  )
}

function StockDetail({ config, selectedKey, monthlyParamsJson, onMonthlyChange, capacityParamsJson, onCapacityChange, activeKey, saving, onSetActive, onSaveParams, onSaveCapacity }: {
  config: StockLogicConfigResponse
  selectedKey: string | null
  monthlyParamsJson: string
  onMonthlyChange: (v: string) => void
  capacityParamsJson: string
  onCapacityChange: (v: string) => void
  activeKey: string
  saving: boolean
  onSetActive: () => void
  onSaveParams: (e: React.FormEvent) => void
  onSaveCapacity: () => void
}) {
  const meta = useMemo(() => (selectedKey ? stockStrategyMeta(selectedKey) : null), [selectedKey])
  if (!selectedKey || !meta) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Seleziona una strategy dalla lista.
      </div>
    )
  }
  const isActive = selectedKey === activeKey

  return (
    <div className="max-w-2xl space-y-6">
      {/* Intestazione */}
      <div className="space-y-1">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-base font-semibold">{meta.label}</h2>
          {isActive && (
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
              Attiva
            </span>
          )}
          {config.is_default && isActive && (
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
              Default di sistema
            </span>
          )}
        </div>
        <p className="text-xs font-mono text-muted-foreground">Key: {selectedKey}</p>
        <p className="text-sm text-muted-foreground mt-1">{meta.description}</p>
      </div>

      {/* Attivazione */}
      {!isActive && (
        <div className="border rounded-lg p-4 bg-muted/20">
          <h3 className="text-sm font-semibold mb-2">Attivazione</h3>
          <p className="text-xs text-muted-foreground mb-3">
            Impostando questa strategy come attiva, il sistema userà i parametri
            qui configurati per calcolare <code className="font-mono">monthly_stock_base_qty</code> di tutti gli articoli.
          </p>
          <button
            type="button"
            onClick={onSetActive}
            disabled={saving}
            className="py-1.5 px-3 rounded-md text-sm font-medium border hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors disabled:opacity-50"
          >
            Imposta come strategy attiva
          </button>
        </div>
      )}

      {/* Parametri monthly base */}
      <form onSubmit={onSaveParams} className="space-y-3 border rounded-lg p-4">
        <div>
          <h3 className="text-sm font-semibold">Parametri monthly base</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            JSON salvato in <code className="font-mono">monthly_base_params_json</code>.
            {!isActive && (
              <span className="ml-1 text-amber-600">
                Salvando si imposta anche questa strategy come attiva.
              </span>
            )}
          </p>
        </div>
        <textarea
          value={monthlyParamsJson}
          onChange={(e) => onMonthlyChange(e.target.value)}
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

      {/* Parametri capacity — sempre visibili */}
      <div className="border rounded-lg p-4 space-y-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">Parametri capacity</h3>
            <span className="text-xs font-mono bg-secondary px-2 py-0.5 rounded">
              {config.capacity_logic_key ?? 'capacity_from_containers_v1'}
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
          onChange={(e) => onCapacityChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-24"
          disabled={saving}
          spellCheck={false}
        />
        <button
          type="button"
          onClick={onSaveCapacity}
          disabled={saving}
          className="py-1.5 px-4 bg-foreground text-background rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {saving ? 'Salvataggio...' : 'Salva parametri capacity'}
        </button>
      </div>
    </div>
  )
}

// ─── Componente principale ────────────────────────────────────────────────────

const DOMAINS: { key: Domain; label: string; description: string }[] = [
  { key: 'proposal', label: 'Proposal', description: 'Logiche di calcolo quantità proposte' },
  { key: 'stock', label: 'Stock', description: 'Strategy di calcolo base mensile e capacity' },
]

export default function AdminLogicConfigPage() {
  const [activeDomain, setActiveDomain] = useState<Domain>('proposal')

  // ── Proposal state ──────────────────────────────────────────────────────────
  const [proposalConfig, setProposalConfig] = useState<ProposalLogicConfigResponse | null>(null)
  const [proposalLoading, setProposalLoading] = useState(true)
  const [proposalSaving, setProposalSaving] = useState(false)
  const [selectedProposalKey, setSelectedProposalKey] = useState<string | null>(null)
  const [proposalParamsJson, setProposalParamsJson] = useState('{}')
  const [defaultLogicKey, setDefaultLogicKey] = useState('')
  const [disabledKeys, setDisabledKeys] = useState<string[]>([])
  const [deleteConfirmKey, setDeleteConfirmKey] = useState<string | null>(null)

  // ── Stock state ─────────────────────────────────────────────────────────────
  const [stockConfig, setStockConfig] = useState<StockLogicConfigResponse | null>(null)
  const [stockLoading, setStockLoading] = useState(true)
  const [stockSaving, setStockSaving] = useState(false)
  const [selectedStockKey, setSelectedStockKey] = useState<string | null>(null)
  const [monthlyParamsJson, setMonthlyParamsJson] = useState('{}')
  const [capacityParamsJson, setCapacityParamsJson] = useState('{}')
  const [activeStrategyKey, setActiveStrategyKey] = useState('')

  // ── Load proposal ───────────────────────────────────────────────────────────
  useEffect(() => {
    setProposalLoading(true)
    apiClient
      .get<ProposalLogicConfigResponse>('/admin/proposal-logic/config')
      .then((r) => applyProposalConfig(r.data))
      .catch(() => toast.error('Impossibile caricare la configurazione proposal'))
      .finally(() => setProposalLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function applyProposalConfig(data: ProposalLogicConfigResponse) {
    setProposalConfig(data)
    setDefaultLogicKey(data.default_logic_key)
    setDisabledKeys(data.disabled_logic_keys ?? [])
    setSelectedProposalKey((prev) => {
      const key = prev && data.known_logics.includes(prev) ? prev : data.default_logic_key
      setProposalParamsJson(JSON.stringify(data.logic_params_by_key[key] ?? {}, null, 2))
      return key
    })
  }

  useEffect(() => {
    if (!proposalConfig || !selectedProposalKey) return
    setProposalParamsJson(JSON.stringify(proposalConfig.logic_params_by_key[selectedProposalKey] ?? {}, null, 2))
  }, [selectedProposalKey]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Load stock ──────────────────────────────────────────────────────────────
  useEffect(() => {
    setStockLoading(true)
    apiClient
      .get<StockLogicConfigResponse>('/admin/stock-logic/config')
      .then((r) => applyStockConfig(r.data))
      .catch(() => toast.error('Impossibile caricare la configurazione logiche stock'))
      .finally(() => setStockLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function applyStockConfig(data: StockLogicConfigResponse) {
    setStockConfig(data)
    setActiveStrategyKey(data.monthly_base_strategy_key)
    setCapacityParamsJson(JSON.stringify(data.capacity_logic_params, null, 2))
    setSelectedStockKey((prev) => {
      const key = prev && data.known_strategies.includes(prev) ? prev : data.monthly_base_strategy_key
      setMonthlyParamsJson(
        key === data.monthly_base_strategy_key
          ? JSON.stringify(data.monthly_base_params, null, 2)
          : (stockStrategyParamsTemplate(key) ?? '{}')
      )
      return key
    })
  }

  useEffect(() => {
    if (!stockConfig || !selectedStockKey) return
    if (selectedStockKey === stockConfig.monthly_base_strategy_key) {
      setMonthlyParamsJson(JSON.stringify(stockConfig.monthly_base_params, null, 2))
    } else {
      setMonthlyParamsJson(stockStrategyParamsTemplate(selectedStockKey) ?? '{}')
    }
  }, [selectedStockKey]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Proposal handlers ───────────────────────────────────────────────────────

  async function saveProposalConfig(overrides: {
    newDefaultKey?: string
    newDisabledKeys?: string[]
    newParams?: Record<string, unknown>
  } = {}) {
    if (!proposalConfig || !selectedProposalKey) return
    let parsedParams: Record<string, unknown>
    try {
      parsedParams = JSON.parse(proposalParamsJson || '{}') as Record<string, unknown>
    } catch {
      toast.error('I parametri devono essere JSON valido')
      return
    }
    const newDefaultKey = overrides.newDefaultKey ?? defaultLogicKey
    const newDisabledKeys = overrides.newDisabledKeys ?? disabledKeys
    const newParams = overrides.newParams ?? parsedParams

    setProposalSaving(true)
    try {
      const { data } = await apiClient.put<ProposalLogicConfigResponse>('/admin/proposal-logic/config', {
        default_logic_key: newDefaultKey,
        logic_params_by_key: {
          ...proposalConfig.logic_params_by_key,
          [selectedProposalKey]: newParams,
        },
        disabled_logic_keys: newDisabledKeys,
      })
      applyProposalConfig(data)
      toast.success('Configurazione salvata')
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setProposalSaving(false)
    }
  }

  function handleProposalToggleEnabled() {
    if (!selectedProposalKey || !proposalConfig) return
    const isDefault = selectedProposalKey === defaultLogicKey
    if (isDefault) {
      toast.error('La logica di default non può essere disabilitata')
      return
    }
    const isEnabled = !disabledKeys.includes(selectedProposalKey)
    const newDisabled = isEnabled
      ? [...disabledKeys, selectedProposalKey]
      : disabledKeys.filter((k) => k !== selectedProposalKey)
    setDisabledKeys(newDisabled)
    void saveProposalConfig({ newDisabledKeys: newDisabled })
  }

  function handleProposalSetDefault() {
    if (!selectedProposalKey || selectedProposalKey === defaultLogicKey || disabledKeys.includes(selectedProposalKey)) return
    setDefaultLogicKey(selectedProposalKey)
    void saveProposalConfig({ newDefaultKey: selectedProposalKey })
  }

  function handleProposalDeleteRequest() {
    if (!selectedProposalKey || selectedProposalKey === defaultLogicKey) return
    setDeleteConfirmKey(selectedProposalKey)
  }

  function handleProposalDeleteConfirm() {
    if (!deleteConfirmKey) return
    const newDisabled = disabledKeys.includes(deleteConfirmKey)
      ? disabledKeys
      : [...disabledKeys, deleteConfirmKey]
    setDisabledKeys(newDisabled)
    setDeleteConfirmKey(null)
    void saveProposalConfig({ newDisabledKeys: newDisabled })
  }

  function handleProposalSaveParams(e: React.FormEvent) {
    e.preventDefault()
    void saveProposalConfig()
  }

  // ── Stock handlers ──────────────────────────────────────────────────────────

  async function saveStockConfig(overrides: { newStrategyKey?: string } = {}) {
    if (!stockConfig || !selectedStockKey) return
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
    const strategyKey = overrides.newStrategyKey ?? activeStrategyKey

    setStockSaving(true)
    try {
      const { data } = await apiClient.put<StockLogicConfigResponse>('/admin/stock-logic/config', {
        monthly_base_strategy_key: strategyKey,
        monthly_base_params: parsedMonthly,
        capacity_logic_params: parsedCapacity,
      })
      applyStockConfig(data)
      toast.success('Configurazione salvata')
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setStockSaving(false)
    }
  }

  function handleStockSetActive() {
    if (!selectedStockKey || selectedStockKey === activeStrategyKey) return
    setActiveStrategyKey(selectedStockKey)
    void saveStockConfig({ newStrategyKey: selectedStockKey })
  }

  function handleStockSaveParams(e: React.FormEvent) {
    e.preventDefault()
    void saveStockConfig()
  }

  // ── Loading state ───────────────────────────────────────────────────────────

  const isLoading = proposalLoading || stockLoading

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b shrink-0">
          <h1 className="text-base font-semibold">Logic Config</h1>
        </div>
        <div className="flex items-center justify-center flex-1 text-sm text-muted-foreground">
          Caricamento...
        </div>
      </div>
    )
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b shrink-0">
        <h1 className="text-base font-semibold">Logic Config</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Governance centralizzata delle logiche operative. Seleziona un dominio per configurarlo.
        </p>
      </div>

      <div className="flex flex-1 overflow-hidden">

        {/* Colonna sinistra — selezione dominio */}
        <div className="w-48 shrink-0 border-r flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b bg-muted/30">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Dominio
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {DOMAINS.map((d) => (
              <button
                key={d.key}
                type="button"
                onClick={() => setActiveDomain(d.key)}
                className={`w-full text-left px-3 py-2.5 rounded-md transition-colors ${
                  activeDomain === d.key
                    ? 'bg-foreground text-background'
                    : 'hover:bg-muted text-foreground'
                }`}
              >
                <div className="text-sm font-medium">{d.label}</div>
                <div className={`text-[11px] mt-0.5 ${activeDomain === d.key ? 'text-background/70' : 'text-muted-foreground'}`}>
                  {d.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Colonna centrale — elenco logiche del dominio */}
        <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
          {activeDomain === 'proposal' && proposalConfig && (
            <ProposalCenter
              config={proposalConfig}
              selectedKey={selectedProposalKey}
              onSelectKey={setSelectedProposalKey}
              defaultLogicKey={defaultLogicKey}
              disabledKeys={disabledKeys}
            />
          )}
          {activeDomain === 'stock' && stockConfig && (
            <StockCenter
              config={stockConfig}
              selectedKey={selectedStockKey}
              onSelectKey={setSelectedStockKey}
              activeKey={activeStrategyKey}
            />
          )}
        </div>

        {/* Colonna destra — configurazione */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeDomain === 'proposal' && proposalConfig && (
            <ProposalDetail
              config={proposalConfig}
              selectedKey={selectedProposalKey}
              paramsJson={proposalParamsJson}
              onParamsChange={setProposalParamsJson}
              defaultLogicKey={defaultLogicKey}
              disabledKeys={disabledKeys}
              saving={proposalSaving}
              onToggleEnabled={handleProposalToggleEnabled}
              onSetDefault={handleProposalSetDefault}
              onDeleteRequest={handleProposalDeleteRequest}
              onSaveParams={handleProposalSaveParams}
            />
          )}
          {activeDomain === 'stock' && stockConfig && (
            <StockDetail
              config={stockConfig}
              selectedKey={selectedStockKey}
              monthlyParamsJson={monthlyParamsJson}
              onMonthlyChange={setMonthlyParamsJson}
              capacityParamsJson={capacityParamsJson}
              onCapacityChange={setCapacityParamsJson}
              activeKey={activeStrategyKey}
              saving={stockSaving}
              onSetActive={handleStockSetActive}
              onSaveParams={handleStockSaveParams}
              onSaveCapacity={() => void saveStockConfig()}
            />
          )}
        </div>
      </div>

      {/* Confirm delete dialog — proposal */}
      {deleteConfirmKey && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-background border rounded-xl shadow-lg w-full max-w-md p-5 space-y-4">
            <h2 className="font-semibold text-base">Rimuovi dal catalogo articoli</h2>
            <p className="text-sm text-muted-foreground">
              La logica{' '}
              <span className="font-mono text-foreground">{deleteConfirmKey}</span>{' '}
              verrà disabilitata e non sarà più assegnabile agli articoli.
              Resterà visibile in questa pagina admin e potrà essere riabilitata.
            </p>
            <p className="text-xs text-muted-foreground">
              Gli articoli già configurati con questa logica continueranno a usarla fino a modifica manuale.
            </p>
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setDeleteConfirmKey(null)}
                className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted transition-colors"
              >
                Annulla
              </button>
              <button
                type="button"
                onClick={handleProposalDeleteConfirm}
                className="py-1.5 px-3 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
              >
                Disabilita logica
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
