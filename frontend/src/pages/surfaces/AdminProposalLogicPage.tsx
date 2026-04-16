/**
 * Admin — Logiche Proposal (TASK-V2-130).
 *
 * Layout a 2 colonne:
 * - sinistra: elenco logiche disponibili con badge enabled/disabled
 * - destra: dettaglio logica selezionata — key, label, descrizione, parametri,
 *           toggle enabled, azione delete (= disable con guardrail)
 *
 * Contratto governance:
 * - una logica disabilitata non compare nel catalogo articoli (ProduzioneHome)
 * - la logica di default non puo essere disabilitata
 * - delete = disable: la logica resta nel registro ma non e assegnabile
 */

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { apiClient } from '@/api/client'
import type { ProposalLogicConfigResponse } from '@/types/api'
import { proposalLogicMeta } from '@/lib/proposalLogicMeta'

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

// ─── Componente principale ────────────────────────────────────────────────────

export default function AdminProposalLogicPage() {
  const [config, setConfig] = useState<ProposalLogicConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Stato di editing lato destra
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [paramsJson, setParamsJson] = useState('{}')
  const [defaultLogicKey, setDefaultLogicKey] = useState('')
  const [disabledKeys, setDisabledKeys] = useState<string[]>([])

  // Confirm delete dialog
  const [deleteConfirmKey, setDeleteConfirmKey] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    apiClient
      .get<ProposalLogicConfigResponse>('/admin/proposal-logic/config')
      .then((r) => {
        applyConfig(r.data)
      })
      .catch(() => toast.error('Impossibile caricare la configurazione proposal'))
      .finally(() => setLoading(false))
  }, [])

  function applyConfig(data: ProposalLogicConfigResponse) {
    setConfig(data)
    setDefaultLogicKey(data.default_logic_key)
    setDisabledKeys(data.disabled_logic_keys ?? [])
    if (!selectedKey || !data.known_logics.includes(selectedKey)) {
      setSelectedKey(data.default_logic_key)
      setParamsJson(JSON.stringify(data.logic_params_by_key[data.default_logic_key] ?? {}, null, 2))
    }
  }

  // Aggiorna params editor quando cambia la logica selezionata
  useEffect(() => {
    if (!config || !selectedKey) return
    setParamsJson(JSON.stringify(config.logic_params_by_key[selectedKey] ?? {}, null, 2))
  }, [selectedKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const isEnabled = (key: string) => !disabledKeys.includes(key)

  const selectedMeta = useMemo(
    () => (selectedKey ? proposalLogicMeta(selectedKey) : null),
    [selectedKey],
  )

  const selectedIsDefault = selectedKey === defaultLogicKey
  const selectedIsEnabled = selectedKey ? isEnabled(selectedKey) : false

  async function saveConfig(overrides: {
    newDefaultKey?: string
    newDisabledKeys?: string[]
    newParams?: Record<string, unknown>
  } = {}) {
    if (!config || !selectedKey) return
    let parsedParams: Record<string, unknown>
    try {
      parsedParams = JSON.parse(paramsJson || '{}') as Record<string, unknown>
    } catch {
      toast.error('I parametri devono essere JSON valido')
      return
    }
    const newDefaultKey = overrides.newDefaultKey ?? defaultLogicKey
    const newDisabledKeys = overrides.newDisabledKeys ?? disabledKeys
    const newParams = overrides.newParams ?? parsedParams

    setSaving(true)
    try {
      const payload = {
        default_logic_key: newDefaultKey,
        logic_params_by_key: {
          ...config.logic_params_by_key,
          [selectedKey]: newParams,
        },
        disabled_logic_keys: newDisabledKeys,
      }
      const { data } = await apiClient.put<ProposalLogicConfigResponse>('/admin/proposal-logic/config', payload)
      applyConfig(data)
      toast.success('Configurazione salvata')
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setSaving(false)
    }
  }

  function handleToggleEnabled() {
    if (!selectedKey || !config) return
    if (selectedIsDefault) {
      toast.error('La logica di default non può essere disabilitata')
      return
    }
    const newDisabled = selectedIsEnabled
      ? [...disabledKeys, selectedKey]
      : disabledKeys.filter((k) => k !== selectedKey)
    setDisabledKeys(newDisabled)
    void saveConfig({ newDisabledKeys: newDisabled })
  }

  function handleSetDefault() {
    if (!selectedKey || selectedIsDefault || !isEnabled(selectedKey)) return
    setDefaultLogicKey(selectedKey)
    void saveConfig({ newDefaultKey: selectedKey })
  }

  function handleDeleteRequest() {
    if (!selectedKey || selectedIsDefault) return
    setDeleteConfirmKey(selectedKey)
  }

  function handleDeleteConfirm() {
    if (!deleteConfirmKey) return
    const newDisabled = disabledKeys.includes(deleteConfirmKey)
      ? disabledKeys
      : [...disabledKeys, deleteConfirmKey]
    setDisabledKeys(newDisabled)
    setDeleteConfirmKey(null)
    void saveConfig({ newDisabledKeys: newDisabled })
  }

  function handleSaveParams(e: React.FormEvent) {
    e.preventDefault()
    void saveConfig()
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b shrink-0">
          <h1 className="text-base font-semibold">Logiche proposal</h1>
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
        <h1 className="text-base font-semibold">Logiche proposal</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Governance del catalogo logiche proposal. Le logiche disabilitate non sono assegnabili agli articoli.
        </p>
      </div>

      {/* Layout 2 colonne */}
      <div className="flex flex-1 overflow-hidden">
        {/* Colonna sinistra — elenco logiche */}
        <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b bg-muted/30">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Logiche disponibili
            </span>
          </div>
          <div className="flex-1 overflow-y-auto divide-y">
            {(config?.known_logics ?? []).map((key) => {
              const meta = proposalLogicMeta(key)
              const enabled = isEnabled(key)
              const isDefault = key === defaultLogicKey
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

          {config?.updated_at && (
            <div className="px-4 py-2 border-t bg-muted/20 text-[11px] text-muted-foreground">
              Aggiornato: {new Date(config.updated_at).toLocaleString('it-IT')}
            </div>
          )}
        </div>

        {/* Colonna destra — dettaglio logica selezionata */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedKey || !selectedMeta ? (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              Seleziona una logica dalla lista.
            </div>
          ) : (
            <div className="max-w-2xl space-y-6">
              {/* Intestazione logica */}
              <div className="space-y-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-base font-semibold">{selectedMeta.label}</h2>
                  {selectedIsDefault && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                      Default globale
                    </span>
                  )}
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    selectedIsEnabled
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {selectedIsEnabled ? 'Abilitata' : 'Disabilitata'}
                  </span>
                </div>
                <p className="text-xs font-mono text-muted-foreground">Key: {selectedKey}</p>
                <p className="text-sm text-muted-foreground mt-1">{selectedMeta.description}</p>
              </div>

              {/* Azioni di governance */}
              <div className="border rounded-lg p-4 space-y-3 bg-muted/20">
                <h3 className="text-sm font-semibold">Governance</h3>

                <div className="flex items-center gap-3 flex-wrap">
                  {/* Toggle enabled */}
                  <button
                    type="button"
                    onClick={handleToggleEnabled}
                    disabled={saving || selectedIsDefault}
                    title={selectedIsDefault ? 'La logica di default non può essere disabilitata' : ''}
                    className={`py-1.5 px-3 rounded-md text-sm font-medium border transition-colors disabled:opacity-50 ${
                      selectedIsEnabled
                        ? 'hover:bg-red-50 hover:text-red-700 hover:border-red-200'
                        : 'hover:bg-green-50 hover:text-green-700 hover:border-green-200'
                    }`}
                  >
                    {selectedIsEnabled ? 'Disabilita logica' : 'Riabilita logica'}
                  </button>

                  {/* Imposta come default */}
                  {!selectedIsDefault && selectedIsEnabled && (
                    <button
                      type="button"
                      onClick={handleSetDefault}
                      disabled={saving}
                      className="py-1.5 px-3 rounded-md text-sm font-medium border hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors disabled:opacity-50"
                    >
                      Imposta come default
                    </button>
                  )}

                  {/* Delete (disable con guardrail) */}
                  {!selectedIsDefault && selectedIsEnabled && (
                    <button
                      type="button"
                      onClick={handleDeleteRequest}
                      disabled={saving}
                      className="py-1.5 px-3 rounded-md text-sm font-medium border border-red-200 text-red-700 hover:bg-red-50 transition-colors disabled:opacity-50"
                    >
                      Rimuovi dal catalogo articoli
                    </button>
                  )}
                </div>

                {selectedIsDefault && (
                  <p className="text-xs text-muted-foreground">
                    La logica di default non può essere disabilitata o rimossa.
                    Per rimuoverla, prima imposta un'altra logica come default.
                  </p>
                )}
              </div>

              {/* Parametri globali */}
              <form onSubmit={handleSaveParams} className="space-y-3 border rounded-lg p-4">
                <h3 className="text-sm font-semibold">Parametri globali</h3>
                <textarea
                  value={paramsJson}
                  onChange={(e) => setParamsJson(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 min-h-40"
                  disabled={saving}
                />
                <div className="flex items-center gap-3">
                  <button
                    type="submit"
                    disabled={saving}
                    className="py-1.5 px-4 bg-foreground text-background rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
                  >
                    {saving ? 'Salvataggio...' : 'Salva parametri'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* Confirm delete dialog */}
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
                onClick={handleDeleteConfirm}
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
