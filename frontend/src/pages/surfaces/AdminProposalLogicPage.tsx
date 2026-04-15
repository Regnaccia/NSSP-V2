import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { apiClient } from '@/api/client'
import type { ProposalLogicConfigResponse } from '@/types/api'

const inputCls =
  'w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

export default function AdminProposalLogicPage() {
  const [config, setConfig] = useState<ProposalLogicConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [defaultLogicKey, setDefaultLogicKey] = useState('')
  const [paramsJson, setParamsJson] = useState('{}')

  const currentParams = useMemo<Record<string, unknown>>(() => {
    if (!config || !defaultLogicKey) return {}
    return config.logic_params_by_key[defaultLogicKey] ?? {}
  }, [config, defaultLogicKey])

  useEffect(() => {
    setLoading(true)
    apiClient
      .get<ProposalLogicConfigResponse>('/admin/proposal-logic/config')
      .then((r) => {
        setConfig(r.data)
        setDefaultLogicKey(r.data.default_logic_key)
        setParamsJson(JSON.stringify(r.data.logic_params_by_key[r.data.default_logic_key] ?? {}, null, 2))
      })
      .catch(() => toast.error('Impossibile caricare la configurazione proposal'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!config || !defaultLogicKey) return
    setParamsJson(JSON.stringify(config.logic_params_by_key[defaultLogicKey] ?? {}, null, 2))
  }, [config, defaultLogicKey])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!config) return
    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(paramsJson || '{}') as Record<string, unknown>
    } catch {
      toast.error('I parametri devono essere JSON valido')
      return
    }
    setSaving(true)
    try {
      const payload = {
        default_logic_key: defaultLogicKey,
        logic_params_by_key: {
          ...config.logic_params_by_key,
          [defaultLogicKey]: parsed,
        },
      }
      const { data } = await apiClient.put<ProposalLogicConfigResponse>('/admin/proposal-logic/config', payload)
      setConfig(data)
      setParamsJson(JSON.stringify(data.logic_params_by_key[data.default_logic_key] ?? {}, null, 2))
      toast.success('Configurazione proposal salvata')
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b shrink-0">
        <h1 className="text-base font-semibold">Logiche proposal</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Suite globale delle logiche proposal V1. L&apos;assegnazione articolo-specifica resta nella surface Articoli.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <p className="text-sm text-muted-foreground">Caricamento...</p>
        ) : (
          <form onSubmit={handleSave} className="space-y-6 max-w-3xl">
            <section className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">Default globale</h2>
                {config?.updated_at && (
                  <span className="text-xs text-muted-foreground">
                    Aggiornato: {new Date(config.updated_at).toLocaleString('it-IT')}
                  </span>
                )}
              </div>

              <label className="block space-y-1">
                <span className="text-sm font-medium">Logic key di default</span>
                <select
                  value={defaultLogicKey}
                  onChange={(e) => setDefaultLogicKey(e.target.value)}
                  className={inputCls}
                  disabled={saving}
                >
                  {(config?.known_logics ?? []).map((logicKey) => (
                    <option key={logicKey} value={logicKey}>
                      {logicKey}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium">Parametri globali della logic attiva</span>
                <textarea
                  value={paramsJson}
                  onChange={(e) => setParamsJson(e.target.value)}
                  className={`${inputCls} min-h-56 font-mono`}
                  disabled={saving}
                />
                <p className="text-xs text-muted-foreground">
                  Valore corrente: <code>{JSON.stringify(currentParams)}</code>
                </p>
              </label>
            </section>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={saving}
                className="py-2 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {saving ? 'Salvataggio...' : 'Salva configurazione'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
