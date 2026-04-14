/**
 * Surface Admin — pagina configurazione logiche stock V1 (TASK-V2-095).
 *
 * Consuma:
 *   GET /api/admin/stock-logic/config  — configurazione attiva + registry strategy
 *   PUT /api/admin/stock-logic/config  — aggiorna strategy, monthly params, capacity params
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'

// ─── Tipi ────────────────────────────────────────────────────────────────────

interface StockLogicConfigResponse {
  monthly_base_strategy_key: string
  monthly_base_params: Record<string, unknown>
  capacity_logic_key: string
  capacity_logic_params: Record<string, unknown>
  is_default: boolean
  updated_at: string | null
  known_strategies: string[]
}

// ─── Helpers UI ───────────────────────────────────────────────────────────────

const inputCls = 'w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'
const btnPrimary = 'py-2 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  )
}

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

// ─── Costanti strategy ────────────────────────────────────────────────────────

const V1_STRATEGY_KEY = 'monthly_stock_base_from_sales_v1'

const V1_PARAM_DEFAULTS: Record<string, string> = {
  windows_months: '12,6,3',
  percentile: '50',
  zscore_threshold: '2.0',
  min_movements: '0',
  min_nonzero_months: '1',
  rounding_scale: '',
}

function parseWindowsMonths(raw: string): number[] | undefined {
  const parts = raw.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n) && n > 0)
  return parts.length > 0 ? parts : undefined
}

// ─── Pagina principale ────────────────────────────────────────────────────────

export default function AdminStockLogicPage() {
  const [config, setConfig] = useState<StockLogicConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<{ ok: boolean; text: string } | null>(null)

  // Campi form strategy + params V1
  const [strategyKey, setStrategyKey] = useState('')
  const [windowsMonths, setWindowsMonths] = useState('')
  const [percentile, setPercentile] = useState('')
  const [zscoreThreshold, setZscoreThreshold] = useState('')
  const [minMovements, setMinMovements] = useState('')
  const [minNonzeroMonths, setMinNonzeroMonths] = useState('')
  const [roundingScale, setRoundingScale] = useState('')

  // Parametri logica capacity fissa (TASK-V2-094)
  const [maxContainerWeightKg, setMaxContainerWeightKg] = useState('')

  const loadConfig = () => {
    setLoading(true)
    apiClient.get<StockLogicConfigResponse>('/admin/stock-logic/config')
      .then(r => {
        const c = r.data
        setConfig(c)
        setStrategyKey(c.monthly_base_strategy_key)
        const p = c.monthly_base_params
        setWindowsMonths(Array.isArray(p.windows_months) ? (p.windows_months as number[]).join(',') : '')
        setPercentile(p.percentile !== undefined ? String(p.percentile) : '')
        setZscoreThreshold(p.zscore_threshold !== undefined ? String(p.zscore_threshold) : '')
        setMinMovements(p.min_movements !== undefined ? String(p.min_movements) : '')
        setMinNonzeroMonths(p.min_nonzero_months !== undefined ? String(p.min_nonzero_months) : '')
        setRoundingScale(p.rounding_scale !== undefined && p.rounding_scale !== null ? String(p.rounding_scale) : '')
        const cp = c.capacity_logic_params
        setMaxContainerWeightKg(cp.max_container_weight_kg !== undefined ? String(cp.max_container_weight_kg) : '')
      })
      .catch(() => toast.error('Impossibile caricare la configurazione logiche stock'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadConfig() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const buildMonthlyParams = (): Record<string, unknown> => {
    const params: Record<string, unknown> = {}
    const wm = parseWindowsMonths(windowsMonths)
    if (wm) params.windows_months = wm
    const p = parseInt(percentile, 10)
    if (!isNaN(p)) params.percentile = p
    const z = parseFloat(zscoreThreshold)
    if (!isNaN(z)) params.zscore_threshold = z
    const mm = parseInt(minMovements, 10)
    if (!isNaN(mm)) params.min_movements = mm
    const mn = parseInt(minNonzeroMonths, 10)
    if (!isNaN(mn)) params.min_nonzero_months = mn
    const rs = parseInt(roundingScale, 10)
    if (!isNaN(rs)) params.rounding_scale = rs
    return params
  }

  const buildCapacityParams = (): Record<string, unknown> => {
    const params: Record<string, unknown> = {}
    const v = parseFloat(maxContainerWeightKg)
    if (!isNaN(v) && v > 0) params.max_container_weight_kg = v
    return params
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaveMsg(null)
    try {
      const { data } = await apiClient.put<StockLogicConfigResponse>('/admin/stock-logic/config', {
        monthly_base_strategy_key: strategyKey,
        monthly_base_params: buildMonthlyParams(),
        capacity_logic_params: buildCapacityParams(),
      })
      setConfig(data)
      setSaveMsg({ ok: true, text: 'Configurazione salvata' })
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (err: unknown) {
      setSaveMsg({ ok: false, text: extractError(err, 'Errore nel salvataggio') })
    } finally {
      setSaving(false)
    }
  }

  const formatDate = (iso: string | null) =>
    iso ? new Date(iso).toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b shrink-0">
        <h1 className="text-base font-semibold">Logiche stock V1</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Strategy di calcolo base mensile e parametri della logica capacity.
        </p>
      </div>

      {/* Contenuto */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <p className="text-sm text-muted-foreground">Caricamento...</p>
        ) : (
          <form onSubmit={handleSave} className="space-y-6 max-w-2xl">

            {/* Strategy monthly_stock_base_qty */}
            <section className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">Strategy — base mensile consumo</h2>
                <div className="flex items-center gap-2">
                  {config?.is_default && (
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">Default di sistema</span>
                  )}
                  {config?.updated_at && (
                    <span className="text-xs text-muted-foreground">Aggiornato: {formatDate(config.updated_at)}</span>
                  )}
                </div>
              </div>

              <Field label="Strategy attiva">
                <select
                  value={strategyKey}
                  onChange={e => setStrategyKey(e.target.value)}
                  disabled={saving}
                  className={inputCls}
                >
                  {(config?.known_strategies ?? [V1_STRATEGY_KEY]).map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>

              {strategyKey === V1_STRATEGY_KEY && (
                <div className="space-y-3 pt-2 border-t">
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Parametri strategy V1</p>
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Finestre mesi (windows_months)">
                      <input
                        type="text"
                        value={windowsMonths}
                        onChange={e => setWindowsMonths(e.target.value)}
                        placeholder={V1_PARAM_DEFAULTS.windows_months}
                        disabled={saving}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground">Valori interi separati da virgola (es. 12,6,3)</p>
                    </Field>
                    <Field label="Percentile">
                      <input
                        type="number"
                        min="0" max="100"
                        value={percentile}
                        onChange={e => setPercentile(e.target.value)}
                        placeholder={V1_PARAM_DEFAULTS.percentile}
                        disabled={saving}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground">0–100 (default 50 = mediana)</p>
                    </Field>
                    <Field label="Z-score threshold">
                      <input
                        type="number"
                        step="0.1" min="0"
                        value={zscoreThreshold}
                        onChange={e => setZscoreThreshold(e.target.value)}
                        placeholder={V1_PARAM_DEFAULTS.zscore_threshold}
                        disabled={saving}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground">Soglia outlier (default 2.0)</p>
                    </Field>
                    <Field label="Min movimenti (min_movements)">
                      <input
                        type="number"
                        min="0" step="1"
                        value={minMovements}
                        onChange={e => setMinMovements(e.target.value)}
                        placeholder={V1_PARAM_DEFAULTS.min_movements}
                        disabled={saving}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground">0 = disabilitato</p>
                    </Field>
                    <Field label="Min mesi non zero (min_nonzero_months)">
                      <input
                        type="number"
                        min="0" step="1"
                        value={minNonzeroMonths}
                        onChange={e => setMinNonzeroMonths(e.target.value)}
                        placeholder={V1_PARAM_DEFAULTS.min_nonzero_months}
                        disabled={saving}
                        className={inputCls}
                      />
                    </Field>
                    <Field label="Arrotondamento (rounding_scale)">
                      <input
                        type="number"
                        min="0" step="1"
                        value={roundingScale}
                        onChange={e => setRoundingScale(e.target.value)}
                        placeholder="nessuno"
                        disabled={saving}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground">Decimali ROUND_HALF_UP (vuoto = nessuno)</p>
                    </Field>
                  </div>
                </div>
              )}
            </section>

            {/* Capacity logic — logica fissa, parametri configurabili */}
            <section className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold">Logica capacity — parametri</h2>
                <span className="text-xs bg-secondary px-2 py-0.5 rounded font-mono">{config?.capacity_logic_key ?? 'capacity_from_containers_v1'}</span>
                <span className="text-xs text-muted-foreground">(logica fissa — non switchabile)</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Formula: <code className="font-mono">capacity = max_container_weight_kg × contenitori / (peso_grammi / 1000)</code>.
                La logica è fissa (DL-ARCH-V2-030 §2); solo i parametri sono configurabili.
              </p>
              <Field label="Peso massimo contenitore (max_container_weight_kg) [kg]">
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={maxContainerWeightKg}
                  onChange={e => setMaxContainerWeightKg(e.target.value)}
                  placeholder="es. 25"
                  disabled={saving}
                  className={`${inputCls} max-w-xs`}
                />
                <p className="text-xs text-muted-foreground">Peso lordo massimo per contenitore in kg (es. 25)</p>
              </Field>
            </section>

            {/* Azioni */}
            <div className="flex items-center gap-3">
              <button type="submit" disabled={saving} className={btnPrimary}>
                {saving ? 'Salvataggio...' : 'Salva configurazione'}
              </button>
              {saveMsg && (
                <p className={`text-xs ${saveMsg.ok ? 'text-green-600' : 'text-red-600'}`}>{saveMsg.text}</p>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
