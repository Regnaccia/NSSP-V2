/**
 * Surface Produzione — Warnings V1 (TASK-V2-078, DL-ARCH-V2-029).
 *
 * Vista operativa consultiva dei warning attivi del modulo Warnings.
 * Mostra warning filtrati per surface 'warnings' (configurazione admin TASK-V2-077).
 *
 * Nessun refresh semantico dedicato: la surface rilegge il read model Warnings
 * gia calcolato dall'ultimo ciclo di rebuild.
 *
 * Endpoint: GET /api/produzione/warnings
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { WarningItem } from '@/types/api'

// ─── Utility ──────────────────────────────────────────────────────────────────

function fmtQty(val: string): string {
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 3 })
}

function fmtDate(val: string): string {
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  return d.toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' })
}

// ─── Badge severita ───────────────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: string }) {
  const cls =
    severity === 'error'
      ? 'bg-red-100 text-red-700'
      : severity === 'warning'
      ? 'bg-amber-100 text-amber-700'
      : 'bg-muted text-muted-foreground'
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cls}`}>
      {severity}
    </span>
  )
}

// ─── Tabella ──────────────────────────────────────────────────────────────────

const thBase =
  'px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b select-none'
const tdCls = 'px-3 py-2 text-sm'
const tdNumCls = `${tdCls} text-right font-mono tabular-nums`

function TabellaWarnings({ items }: { items: WarningItem[] }) {
  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-background">
          <tr>
            <th className={thBase}>Tipo</th>
            <th className={thBase}>Sev.</th>
            <th className={thBase}>Articolo</th>
            <th className={thBase}>Messaggio</th>
            <th className={`${thBase} text-right`}>Giacenza</th>
            <th className={`${thBase} text-right`}>Anomalia</th>
            <th className={`${thBase} text-right`}>Rilevato il</th>
          </tr>
        </thead>
        <tbody>
          {items.map((w) => (
            <tr
              key={w.warning_id}
              className="border-b last:border-b-0 hover:bg-muted/30 transition-colors"
            >
              <td className={tdCls}>
                <span className="font-mono text-xs">{w.type}</span>
              </td>
              <td className={tdCls}>
                <SeverityBadge severity={w.severity} />
              </td>
              <td className={tdCls}>
                <span className="font-mono text-xs">{w.article_code}</span>
              </td>
              <td className={tdCls}>
                <span className="text-muted-foreground">{w.message}</span>
              </td>
              <td className={`${tdNumCls} text-red-600`}>{fmtQty(w.stock_calculated)}</td>
              <td className={tdNumCls}>{fmtQty(w.anomaly_qty)}</td>
              <td className={`${tdNumCls} text-muted-foreground`}>{fmtDate(w.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function WarningsPage() {
  const [items, setItems] = useState<WarningItem[]>([])
  const [loadStatus, setLoadStatus] = useState<'loading' | 'idle' | 'error'>('loading')

  useEffect(() => {
    apiClient
      .get<WarningItem[]>('/produzione/warnings')
      .then((r) => {
        setItems(r.data)
        setLoadStatus('idle')
      })
      .catch(() => {
        setLoadStatus('error')
        toast.error('Impossibile caricare i warning')
      })
  }, [])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/30 text-xs text-muted-foreground shrink-0">
        <span className="font-medium text-foreground">Avvertimenti</span>

        {loadStatus === 'idle' && (
          <span
            className={`px-2 py-0.5 rounded font-medium ${
              items.length > 0 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
            }`}
          >
            {items.length > 0
              ? `${items.length} avvertiment${items.length === 1 ? 'o' : 'i'}`
              : 'Nessun avvertimento'}
          </span>
        )}

        {loadStatus === 'error' && (
          <span className="px-2 py-0.5 rounded font-medium bg-red-100 text-red-700">
            Errore caricamento
          </span>
        )}
      </div>

      {/* Contenuto */}
      {loadStatus === 'loading' && (
        <div className="flex items-center justify-center flex-1 p-12 text-muted-foreground text-sm">
          Caricamento…
        </div>
      )}

      {loadStatus === 'error' && (
        <div className="flex items-center justify-center flex-1 p-12 text-red-600 text-sm">
          Impossibile caricare i dati. Riprovare.
        </div>
      )}

      {loadStatus === 'idle' && items.length === 0 && (
        <div className="flex flex-col items-center justify-center flex-1 p-12 text-muted-foreground">
          <p className="text-sm">Nessun avvertimento attivo.</p>
          <p className="text-xs mt-1">La giacenza di tutti gli articoli è nella norma.</p>
        </div>
      )}

      {loadStatus === 'idle' && items.length > 0 && <TabellaWarnings items={items} />}
    </div>
  )
}
