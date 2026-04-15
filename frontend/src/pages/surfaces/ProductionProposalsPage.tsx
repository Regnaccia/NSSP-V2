import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { apiClient } from '@/api/client'
import type {
  ProductionProposalItem,
  ProductionProposalReconcileResult,
  ProductionProposalWorkflowStatus,
  ProposalWorkspaceDetail,
  ProposalWorkspaceRowItem,
} from '@/types/api'

type LoadStatus = 'loading' | 'idle' | 'error'

function fmtQty(val: string | null): string {
  if (val == null) return '-'
  const n = parseFloat(val)
  return Number.isNaN(n) ? val : n.toLocaleString('it-IT', { maximumFractionDigits: 3 })
}

function fmtMm(val: string | null): string {
  if (val == null) return '-'
  const n = parseFloat(val)
  return Number.isNaN(n) ? val : n.toLocaleString('it-IT', { maximumFractionDigits: 4 })
}

function DescrizioneParts({ parts, fallback }: { parts: string[]; fallback: string }) {
  if (parts.length === 0) {
    return <span className="text-muted-foreground italic text-xs">{fallback || '-'}</span>
  }
  return (
    <div className="space-y-0.5">
      {parts.map((part, i) => (
        <div key={i} className={i === 0 ? 'font-medium text-sm' : 'text-xs text-muted-foreground'}>
          {part}
        </div>
      ))}
    </div>
  )
}

function fmtDate(val: string | null): string {
  if (!val) return '-'
  const d = new Date(`${val}T00:00:00`)
  return Number.isNaN(d.getTime()) ? val : d.toLocaleDateString('it-IT')
}

function fmtDateTime(val: string): string {
  return new Date(val).toLocaleString('it-IT')
}

function warningLabel(code: string): string {
  if (code === 'INVALID_STOCK_CAPACITY') return 'Capacity'
  if (code === 'MISSING_RAW_BAR_LENGTH') return 'Barra mancante'
  return code
}

function proposalLogicLabel(logicKey: string): string {
  if (logicKey === 'proposal_target_pieces_v1') return 'Pezzi'
  if (logicKey === 'proposal_full_bar_v1') return 'Barra intera'
  if (logicKey === 'proposal_required_qty_total_v1') return 'Pezzi'
  return logicKey
}

function downloadCsv(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function WorkspaceOverrideModal({
  row,
  saving,
  onClose,
  onSave,
}: {
  row: ProposalWorkspaceRowItem
  saving: boolean
  onClose: () => void
  onSave: (overrideQty: string, overrideReason: string) => Promise<void>
}) {
  const [overrideQty, setOverrideQty] = useState(row.override_qty ?? '')
  const [overrideReason, setOverrideReason] = useState(row.override_reason ?? '')

  useEffect(() => {
    setOverrideQty(row.override_qty ?? '')
    setOverrideReason(row.override_reason ?? '')
  }, [row.row_id, row.override_qty, row.override_reason])

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-background border rounded-xl shadow-lg w-full max-w-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-base">Override workspace row</h2>
            <p className="text-xs text-muted-foreground font-mono">
              #{row.row_id} · {row.article_code}
            </p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none">
            ×
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Descrizione</p>
            <p>{row.display_description}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Driver</p>
            <p>{row.primary_driver ?? '-'}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Qty richiesta totale</p>
            <p>{fmtQty(row.required_qty_total)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Qty proposta</p>
            <p>{fmtQty(row.proposed_qty)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-xs text-muted-foreground">Warning attivi</p>
            <div className="flex gap-1 flex-wrap mt-1">
              {row.active_warning_codes.length === 0 ? (
                <span className="text-muted-foreground/60 italic">nessuno</span>
              ) : (
                row.active_warning_codes.map((code) => (
                  <span key={code} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                    {warningLabel(code)}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <label className="block space-y-1">
            <span className="text-xs text-muted-foreground">Override qty</span>
            <input
              type="text"
              value={overrideQty}
              onChange={(e) => setOverrideQty(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm font-mono"
              disabled={saving}
            />
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted-foreground">Motivo override</span>
            <textarea
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm min-h-24"
              disabled={saving}
            />
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} disabled={saving} className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted">
            Chiudi
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => onSave(overrideQty, overrideReason)}
            className="py-1.5 px-3 rounded-md text-sm font-medium bg-foreground text-background disabled:opacity-50"
          >
            {saving ? 'Salvataggio...' : 'Salva override'}
          </button>
        </div>
      </div>
    </div>
  )
}

function WarningBadges({ codes }: { codes: string[] }) {
  if (codes.length === 0) {
    return <span className="text-muted-foreground/60 italic">-</span>
  }
  return (
    <div className="flex flex-wrap gap-1">
      {codes.map((code) => (
        <span key={code} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
          {warningLabel(code)}
        </span>
      ))}
    </div>
  )
}

function WorkspaceView({
  workspaceId,
  navigate,
}: {
  workspaceId: string
  navigate: ReturnType<typeof useNavigate>
}) {
  const [workspace, setWorkspace] = useState<ProposalWorkspaceDetail | null>(null)
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [overrideRow, setOverrideRow] = useState<ProposalWorkspaceRowItem | null>(null)

  const loadWorkspace = async () => {
    setLoadStatus('loading')
    try {
      const { data } = await apiClient.get<ProposalWorkspaceDetail>(`/produzione/proposals/workspaces/${workspaceId}`)
      setWorkspace(data)
      setLoadStatus('idle')
    } catch {
      setLoadStatus('error')
    }
  }

  useEffect(() => {
    loadWorkspace()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId])

  const handleSaveOverride = async (overrideQtyRaw: string, overrideReason: string) => {
    if (!overrideRow) return
    const parsed = overrideQtyRaw.trim() === '' ? null : Number.parseFloat(overrideQtyRaw.replace(',', '.'))
    if (overrideQtyRaw.trim() !== '' && Number.isNaN(parsed)) {
      toast.error('Override qty non valido')
      return
    }
    setBusyAction(`override-${overrideRow.row_id}`)
    try {
      const { data } = await apiClient.patch<ProposalWorkspaceDetail>(
        `/produzione/proposals/workspaces/${workspaceId}/rows/${overrideRow.row_id}/override`,
        { override_qty: parsed, override_reason: overrideReason || null },
      )
      setWorkspace(data)
      const refreshed = data.rows.find((row) => row.row_id === overrideRow.row_id) ?? null
      setOverrideRow(refreshed)
      toast.success('Override salvato')
    } catch (err: unknown) {
      const detailMsg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detailMsg ?? 'Errore durante il salvataggio override')
    } finally {
      setBusyAction(null)
    }
  }

  const handleExport = async () => {
    setBusyAction('export')
    try {
      const response = await apiClient.post<Blob>(
        `/produzione/proposals/workspaces/${workspaceId}/export`,
        undefined,
        { responseType: 'blob' },
      )
      const batchId = response.headers['x-export-batch-id']
      const disposition = response.headers['content-disposition'] as string | undefined
      const filenameMatch = disposition?.match(/filename=\"?([^"]+)\"?/)
      const filename = filenameMatch?.[1] ?? 'production-proposals.csv'
      downloadCsv(new Blob([response.data], { type: 'text/csv' }), filename)
      toast.success(`Workspace esportato${batchId ? ` · batch ${batchId}` : ''}`)
      navigate('/produzione/proposals', { replace: true })
    } catch (err: unknown) {
      const blob = (err as { response?: { data?: Blob } })?.response?.data
      if (blob instanceof Blob) {
        const text = await blob.text()
        try {
          const parsed = JSON.parse(text) as { detail?: string }
          toast.error(parsed.detail ?? "Errore durante l'export")
        } catch {
          toast.error("Errore durante l'export")
        }
      } else {
        toast.error("Errore durante l'export")
      }
    } finally {
      setBusyAction(null)
    }
  }

  const handleAbandon = async () => {
    setBusyAction('abandon')
    try {
      await apiClient.post(`/produzione/proposals/workspaces/${workspaceId}/abandon`)
      toast.success('Workspace annullato')
      navigate('/produzione/planning-candidates', { replace: true })
    } catch (err: unknown) {
      const detailMsg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detailMsg ?? 'Impossibile annullare il workspace')
    } finally {
      setBusyAction(null)
    }
  }

  if (loadStatus === 'loading') {
    return <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">Caricamento workspace...</div>
  }

  if (loadStatus === 'error' || workspace == null) {
    return <div className="flex-1 flex items-center justify-center text-sm text-red-600">Workspace non trovato o non disponibile.</div>
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b bg-muted/30 flex items-center gap-3 shrink-0">
        <div>
          <h1 className="text-sm font-semibold text-foreground">Production Proposals · Workspace</h1>
          <p className="text-xs text-muted-foreground">
            Snapshot temporaneo dei candidate selezionati · {workspace.rows.length} righe
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            Scade: {fmtDateTime(workspace.expires_at)}
          </span>
          <button
            onClick={loadWorkspace}
            disabled={busyAction !== null}
            className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted disabled:opacity-50"
          >
            Aggiorna vista
          </button>
          <button
            onClick={handleAbandon}
            disabled={busyAction !== null || workspace.status !== 'open'}
            className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted disabled:opacity-50"
          >
            Chiudi senza esportare
          </button>
          <button
            onClick={handleExport}
            disabled={busyAction !== null || workspace.status !== 'open' || workspace.rows.length === 0}
            className="py-1.5 px-3 rounded-md text-sm font-medium bg-foreground text-background disabled:opacity-50"
          >
            {busyAction === 'export' ? 'Export...' : 'Esporta'}
          </button>
        </div>
      </div>

      {workspace.status !== 'open' && (
        <div className="px-4 py-3 border-b bg-amber-50 text-amber-800 text-sm">
          Workspace in stato <span className="font-medium">{workspace.status}</span>. Non è più modificabile.
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <table className="border-collapse" style={{ minWidth: '1200px', width: '100%' }}>
          <thead className="sticky top-0 bg-background z-10">
            <tr>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Cliente / Dest.</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Codice</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Descrizione</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Immagine</th>
              <th className="px-3 py-2 border-b text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Qtà</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Materiale</th>
              <th className="px-3 py-2 border-b text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">mm Mat.</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Ordine</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Note</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">User</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Warnings</th>
              <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {workspace.rows.map((row) => (
              <tr key={row.row_id} className="border-b hover:bg-muted/30">
                <td className="px-3 py-2 align-top text-xs text-muted-foreground max-w-[140px]">
                  {row.requested_destination_display ?? '-'}
                </td>
                <td className="px-3 py-2 align-top whitespace-nowrap">
                  <div className="font-mono text-xs">{row.article_code}</div>
                  <div className="text-[10px] text-muted-foreground">#{row.row_id}</div>
                </td>
                <td className="px-3 py-2 align-top min-w-[180px]">
                  <DescrizioneParts parts={row.description_parts} fallback={row.display_description} />
                </td>
                <td className="px-3 py-2 align-top font-mono text-xs whitespace-nowrap">
                  {row.codice_immagine ?? '-'}
                </td>
                <td className="px-3 py-2 align-top text-right font-mono text-sm font-semibold whitespace-nowrap">
                  {fmtQty(row.final_qty)}
                  <div className="text-[10px] text-muted-foreground font-normal">{proposalLogicLabel(row.proposal_logic_key)}</div>
                  {row.override_qty != null && (
                    <div className="text-[10px] text-amber-600 font-normal">ov. {fmtQty(row.override_qty)}</div>
                  )}
                </td>
                <td className="px-3 py-2 align-top text-xs whitespace-nowrap">
                  {row.materiale ?? '-'}
                </td>
                <td className="px-3 py-2 align-top text-right font-mono text-xs whitespace-nowrap">
                  {fmtMm(row.mm_materiale)}
                </td>
                <td className="px-3 py-2 align-top text-xs whitespace-nowrap">
                  {row.ordine ? (
                    <span className="font-mono">{row.ordine}</span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                  {row.ordine_linea_mancante && (
                    <div className="text-[10px] text-red-600 font-medium mt-0.5">riga mancante</div>
                  )}
                </td>
                <td className="px-3 py-2 align-top text-xs text-muted-foreground max-w-[120px]">
                  {row.note_preview || '-'}
                </td>
                <td className="px-3 py-2 align-top text-xs text-muted-foreground whitespace-nowrap">
                  {row.user_preview}
                </td>
                <td className="px-3 py-2 align-top">
                  <WarningBadges codes={row.active_warning_codes} />
                </td>
                <td className="px-3 py-2 align-top whitespace-nowrap">
                  <button
                    onClick={() => setOverrideRow(row)}
                    disabled={busyAction !== null || workspace.status !== 'open'}
                    className="px-2 py-1 border rounded text-xs hover:bg-muted disabled:opacity-50"
                  >
                    Override
                  </button>
                  <div className="text-[10px] text-muted-foreground mt-1">{fmtDateTime(row.updated_at)}</div>
                </td>
              </tr>
            ))}
            {workspace.rows.length === 0 && (
              <tr>
                <td colSpan={12} className="px-3 py-10 text-center text-sm text-muted-foreground">
                  Workspace vuoto.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {overrideRow && (
        <WorkspaceOverrideModal
          row={overrideRow}
          saving={busyAction === `override-${overrideRow.row_id}`}
          onClose={() => setOverrideRow(null)}
          onSave={handleSaveOverride}
        />
      )}
    </div>
  )
}

function HistoryView() {
  const [items, setItems] = useState<ProductionProposalItem[]>([])
  const [statusFilter, setStatusFilter] = useState<ProductionProposalWorkflowStatus | 'all'>('all')
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [busyAction, setBusyAction] = useState<string | null>(null)

  const load = async () => {
    setLoadStatus('loading')
    try {
      const { data } = await apiClient.get<ProductionProposalItem[]>('/produzione/proposals/exported', {
        params: statusFilter === 'all' ? undefined : { workflow_status: statusFilter },
      })
      setItems(data)
      setLoadStatus('idle')
    } catch {
      setLoadStatus('error')
    }
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter])

  const allSelected = items.length > 0 && selectedIds.length === items.length

  const selectedItems = useMemo(
    () => items.filter((item) => selectedIds.includes(item.proposal_id)),
    [items, selectedIds],
  )

  const handleReconcile = async () => {
    setBusyAction('reconcile')
    try {
      const { data } = await apiClient.post<ProductionProposalReconcileResult>(
        '/produzione/proposals/exported/reconcile',
        { proposal_ids: selectedIds.length > 0 ? selectedIds : null },
      )
      toast.success(`Riconciliazione completata: ${data.matched} matched, ${data.unmatched} unmatched`)
      setSelectedIds([])
      await load()
    } catch {
      toast.error('Errore durante la riconciliazione')
    } finally {
      setBusyAction(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b bg-muted/30 flex items-center gap-3 shrink-0">
        <div>
          <h1 className="text-sm font-semibold text-foreground">Production Proposals · Exported History</h1>
          <p className="text-xs text-muted-foreground">Storico persistente delle proposal esportate e riconciliate.</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ProductionProposalWorkflowStatus | 'all')}
            className="px-2 py-1 border rounded-md text-sm"
          >
            <option value="all">Tutti gli stati</option>
            <option value="exported">Exported</option>
            <option value="reconciled">Reconciled</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button onClick={load} disabled={busyAction !== null} className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted disabled:opacity-50">
            Aggiorna
          </button>
          <button
            onClick={handleReconcile}
            disabled={busyAction !== null || items.length === 0}
            className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted disabled:opacity-50"
          >
            Reconcile
          </button>
        </div>
      </div>

      {loadStatus === 'loading' && (
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">Caricamento...</div>
      )}
      {loadStatus === 'error' && (
        <div className="flex-1 flex items-center justify-center text-sm text-red-600">Impossibile caricare lo storico proposal</div>
      )}
      {loadStatus === 'idle' && (
        <div className="flex-1 overflow-auto">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-background">
              <tr>
                <th className="px-3 py-2 border-b text-left">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => setSelectedIds(allSelected ? [] : items.map((item) => item.proposal_id))}
                  />
                </th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Codice</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Descrizione</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Planning</th>
                <th className="px-3 py-2 border-b text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty richiesta</th>
                <th className="px-3 py-2 border-b text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty finale</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Warnings</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Stato</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">ODE_REF</th>
                <th className="px-3 py-2 border-b text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Aggiornato</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.proposal_id} className="border-b hover:bg-muted/30">
                  <td className="px-3 py-2 align-top">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.proposal_id)}
                      onChange={() => {
                        setSelectedIds((prev) => (
                          prev.includes(item.proposal_id)
                            ? prev.filter((id) => id !== item.proposal_id)
                            : [...prev, item.proposal_id]
                        ))
                      }}
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="font-mono text-xs">{item.article_code}</div>
                    <div className="text-[11px] text-muted-foreground">#{item.proposal_id}</div>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="font-medium">{item.display_description}</div>
                    {(item.order_reference || item.line_reference) && (
                      <div className="text-xs text-muted-foreground">
                        {item.order_reference ?? '-'}{item.line_reference != null ? ` / ${item.line_reference}` : ''}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top text-sm">
                    <div>{item.planning_mode ?? '-'}</div>
                    <div className="text-xs text-muted-foreground">{item.primary_driver ?? '-'}</div>
                  </td>
                  <td className="px-3 py-2 align-top text-right font-mono">{fmtQty(item.required_qty_total)}</td>
                  <td className="px-3 py-2 align-top text-right font-mono font-semibold">{fmtQty(item.final_qty)}</td>
                  <td className="px-3 py-2 align-top">
                    <WarningBadges codes={item.active_warning_codes} />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="text-sm">{item.workflow_status}</div>
                    {item.reconciled_production_id_dettaglio != null && (
                      <div className="text-xs text-muted-foreground">
                        {item.reconciled_production_bucket} · {item.reconciled_production_id_dettaglio}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top font-mono text-xs">{item.ode_ref}</td>
                  <td className="px-3 py-2 align-top text-xs text-muted-foreground">{fmtDateTime(item.updated_at)}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-3 py-10 text-center text-sm text-muted-foreground">
                    Nessuna proposal esportata disponibile.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {selectedItems.length > 0 && (
            <div className="px-4 py-2 border-t bg-muted/20 text-xs text-muted-foreground">
              {selectedItems.length} proposal selezionate
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ProductionProposalsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const workspaceId = searchParams.get('workspace_id')

  if (workspaceId) {
    return <WorkspaceView workspaceId={workspaceId} navigate={navigate} />
  }
  return <HistoryView />
}
