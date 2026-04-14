/**
 * Surface Produzione — tabella gestione famiglie articolo (TASK-V2-025, TASK-V2-026, TASK-V2-066, TASK-V2-093).
 *
 * Consuma:
 *   GET   /api/produzione/famiglie/catalog                              — tutte le famiglie + is_active + n_articoli
 *   POST  /api/produzione/famiglie                                      — crea nuova famiglia
 *   PATCH /api/produzione/famiglie/{code}/active                        — toggle is_active
 *   PATCH /api/produzione/famiglie/{code}/considera-produzione          — toggle considera_in_produzione (default planning)
 *   PATCH /api/produzione/famiglie/{code}/aggrega-codice-produzione     — toggle planning_mode default (by_article / by_customer_order_line)
 *   PATCH /api/produzione/famiglie/{code}/stock-policy                  — imposta stock_months e stock_trigger_months (TASK-V2-093)
 *   PATCH /api/produzione/famiglie/{code}/gestione-scorte               — toggle gestione_scorte_attiva (TASK-V2-097)
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { FamigliaRow } from '@/types/api'

const inputCls =
  'px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'

const inputSmCls =
  'w-20 px-2 py-1 border rounded text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50'

// ─── Form creazione famiglia ──────────────────────────────────────────────────

function FormCreaFamiglia({ onCreated }: { onCreated: (row: FamigliaRow) => void }) {
  const [code, setCode] = useState('')
  const [label, setLabel] = useState('')
  const [sortOrder, setSortOrder] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim() || !label.trim()) return
    setSaving(true)
    try {
      const { data } = await apiClient.post<FamigliaRow>('/produzione/famiglie', {
        code: code.trim(),
        label: label.trim(),
        sort_order: sortOrder.trim() ? parseInt(sortOrder, 10) : null,
      })
      onCreated(data)
      setCode('')
      setLabel('')
      setSortOrder('')
      toast.success(`Famiglia "${data.label}" creata`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail ?? 'Errore durante la creazione')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3 flex-wrap">
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Codice *</label>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="es. conto_lavorazione"
          className={`${inputCls} w-48`}
          disabled={saving}
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Label *</label>
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="es. Conto lavorazione"
          className={`${inputCls} w-52`}
          disabled={saving}
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Ordine</label>
        <input
          type="number"
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
          placeholder="es. 6"
          className={`${inputCls} w-24`}
          disabled={saving}
        />
      </div>
      <button
        type="submit"
        disabled={saving || !code.trim() || !label.trim()}
        className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {saving ? 'Creazione…' : 'Crea famiglia'}
      </button>
    </form>
  )
}

// ─── Riga tabella con toggle ──────────────────────────────────────────────────

function RigaFamiglia({
  famiglia,
  onToggled,
}: {
  famiglia: FamigliaRow
  onToggled: (updated: FamigliaRow) => void
}) {
  const [togglingActive, setTogglingActive] = useState(false)
  const [togglingProd, setTogglingProd] = useState(false)
  const [togglingAggrega, setTogglingAggrega] = useState(false)
  const [togglingGestione, setTogglingGestione] = useState(false)

  // Stock policy state — inizializza dai valori attuali della famiglia
  const [stockMonths, setStockMonths] = useState(famiglia.stock_months ?? '')
  const [stockTrigger, setStockTrigger] = useState(famiglia.stock_trigger_months ?? '')
  const [savingStock, setSavingStock] = useState(false)

  // Traccia se i valori sono stati modificati rispetto al server
  const originalStockMonths = famiglia.stock_months ?? ''
  const originalStockTrigger = famiglia.stock_trigger_months ?? ''
  const stockDirty = stockMonths !== originalStockMonths || stockTrigger !== originalStockTrigger

  const handleToggleActive = async () => {
    setTogglingActive(true)
    try {
      const { data } = await apiClient.patch<FamigliaRow>(
        `/produzione/famiglie/${encodeURIComponent(famiglia.code)}/active`
      )
      onToggled(data)
    } catch {
      toast.error('Impossibile aggiornare lo stato della famiglia')
    } finally {
      setTogglingActive(false)
    }
  }

  const handleToggleProd = async () => {
    setTogglingProd(true)
    try {
      const { data } = await apiClient.patch<FamigliaRow>(
        `/produzione/famiglie/${encodeURIComponent(famiglia.code)}/considera-produzione`
      )
      onToggled(data)
    } catch {
      toast.error('Impossibile aggiornare il flag produzione')
    } finally {
      setTogglingProd(false)
    }
  }

  const handleToggleAggrega = async () => {
    setTogglingAggrega(true)
    try {
      const { data } = await apiClient.patch<FamigliaRow>(
        `/produzione/famiglie/${encodeURIComponent(famiglia.code)}/aggrega-codice-produzione`
      )
      onToggled(data)
    } catch {
      toast.error('Impossibile aggiornare la modalità planning')
    } finally {
      setTogglingAggrega(false)
    }
  }

  const handleToggleGestione = async () => {
    setTogglingGestione(true)
    try {
      const { data } = await apiClient.patch<FamigliaRow>(
        `/produzione/famiglie/${encodeURIComponent(famiglia.code)}/gestione-scorte`
      )
      onToggled(data)
    } catch {
      toast.error('Impossibile aggiornare il flag gestione scorte')
    } finally {
      setTogglingGestione(false)
    }
  }

  const handleSaveStock = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingStock(true)
    try {
      const { data } = await apiClient.patch<FamigliaRow>(
        `/produzione/famiglie/${encodeURIComponent(famiglia.code)}/stock-policy`,
        {
          stock_months: stockMonths !== '' ? parseFloat(stockMonths) : null,
          stock_trigger_months: stockTrigger !== '' ? parseFloat(stockTrigger) : null,
        }
      )
      onToggled(data)
      toast.success(`Stock policy "${famiglia.label}" aggiornata`)
    } catch {
      toast.error('Impossibile salvare la stock policy')
    } finally {
      setSavingStock(false)
    }
  }

  return (
    <tr className={`border-b last:border-b-0 ${!famiglia.is_active ? 'opacity-50' : ''}`}>
      <td className="py-2.5 pr-4 text-muted-foreground tabular-nums text-sm">
        {famiglia.sort_order ?? '—'}
      </td>
      <td className="py-2.5 pr-4 font-mono text-xs">{famiglia.code}</td>
      <td className="py-2.5 pr-4 font-medium text-sm">{famiglia.label}</td>
      <td className="py-2.5 pr-4 text-right tabular-nums text-sm">
        {famiglia.n_articoli > 0 ? famiglia.n_articoli : (
          <span className="text-muted-foreground">—</span>
        )}
      </td>
      <td className="py-2.5 pr-4">
        {famiglia.is_active ? (
          <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700 font-medium">
            Attiva
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded text-xs bg-muted text-muted-foreground font-medium">
            Inattiva
          </span>
        )}
      </td>
      <td className="py-2.5 pr-4 text-center">
        <input
          type="checkbox"
          checked={famiglia.considera_in_produzione}
          onChange={handleToggleProd}
          disabled={togglingProd}
          className="h-4 w-4 cursor-pointer accent-primary disabled:cursor-wait"
          title={famiglia.considera_in_produzione ? 'Nel perimetro produzione' : 'Fuori perimetro produzione'}
        />
      </td>
      <td className="py-2.5 pr-4 text-center">
        <input
          type="checkbox"
          checked={famiglia.aggrega_codice_in_produzione}
          onChange={handleToggleAggrega}
          disabled={togglingAggrega}
          className="h-4 w-4 cursor-pointer accent-primary disabled:cursor-wait"
          title={famiglia.aggrega_codice_in_produzione ? 'by_article — aggrega per codice articolo' : 'by_customer_order_line — per riga ordine cliente'}
        />
      </td>
      <td className="py-2.5 pr-4 text-center">
        <input
          type="checkbox"
          checked={famiglia.gestione_scorte_attiva}
          onChange={handleToggleGestione}
          disabled={togglingGestione}
          className="h-4 w-4 cursor-pointer accent-primary disabled:cursor-wait"
          title={famiglia.gestione_scorte_attiva ? 'Gestione scorte attiva' : 'Gestione scorte non attiva'}
        />
      </td>
      {/* Stock policy defaults — solo rilevanti per by_article con gestione scorte attiva */}
      <td className="py-2.5 pr-2">
        <form onSubmit={handleSaveStock} className="flex items-center gap-1.5">
          <input
            type="number"
            step="0.5"
            min="0"
            value={stockMonths}
            onChange={(e) => setStockMonths(e.target.value)}
            placeholder="—"
            disabled={savingStock}
            className={inputSmCls}
            title="Mesi di stock target (by_article)"
          />
          <input
            type="number"
            step="0.5"
            min="0"
            value={stockTrigger}
            onChange={(e) => setStockTrigger(e.target.value)}
            placeholder="—"
            disabled={savingStock}
            className={inputSmCls}
            title="Mesi di trigger riordine (by_article)"
          />
          <button
            type="submit"
            disabled={savingStock || !stockDirty}
            className="text-xs px-2 py-1 border rounded text-primary border-primary hover:bg-primary/10 disabled:opacity-40 disabled:cursor-default transition-colors"
          >
            {savingStock ? '…' : 'Salva'}
          </button>
        </form>
      </td>
      <td className="py-2.5">
        <button
          onClick={handleToggleActive}
          disabled={togglingActive}
          className="text-xs text-muted-foreground hover:text-foreground underline disabled:opacity-50 transition-colors"
        >
          {togglingActive ? '…' : famiglia.is_active ? 'Disattiva' : 'Attiva'}
        </button>
      </td>
    </tr>
  )
}

// ─── Pagina principale ────────────────────────────────────────────────────────

export default function FamigliePage() {
  const [famiglie, setFamiglie] = useState<FamigliaRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    apiClient
      .get<FamigliaRow[]>('/produzione/famiglie/catalog')
      .then((r) => setFamiglie(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const handleCreated = (row: FamigliaRow) => {
    setFamiglie((prev) => [...prev, row].sort((a, b) => {
      if (a.sort_order !== null && b.sort_order !== null) return a.sort_order - b.sort_order
      if (a.sort_order !== null) return -1
      if (b.sort_order !== null) return 1
      return a.code.localeCompare(b.code)
    }))
  }

  const handleToggled = (updated: FamigliaRow) => {
    setFamiglie((prev) => prev.map((f) => (f.code === updated.code ? updated : f)))
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b shrink-0">
        <h1 className="text-base font-semibold">Famiglie articolo</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Catalogo interno delle famiglie usate per classificare gli articoli.
        </p>
      </div>

      {/* Contenuto */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Form creazione */}
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Nuova famiglia
          </h2>
          <FormCreaFamiglia onCreated={handleCreated} />
        </section>

        {/* Tabella */}
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Catalogo
          </h2>
          <p className="text-xs text-muted-foreground">
            I campi <em>Stock mesi</em> e <em>Trigger mesi</em> valgono solo per articoli con planning mode <strong>by_article</strong> e <em>Gestione scorte</em> attiva.
          </p>

          {loading && <p className="text-sm text-muted-foreground">Caricamento…</p>}
          {error && <p className="text-sm text-red-600">Impossibile caricare il catalogo famiglie.</p>}

          {!loading && !error && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b text-xs text-muted-foreground uppercase tracking-wide">
                    <th className="text-left py-2 pr-4 font-medium w-12">Ord.</th>
                    <th className="text-left py-2 pr-4 font-medium">Codice</th>
                    <th className="text-left py-2 pr-4 font-medium">Label</th>
                    <th className="text-right py-2 pr-4 font-medium">Articoli</th>
                    <th className="text-left py-2 pr-4 font-medium">Stato</th>
                    <th className="text-center py-2 pr-4 font-medium" title="Default planning: articoli nel perimetro produzione">In produzione</th>
                    <th className="text-center py-2 pr-4 font-medium" title="Planning mode default della famiglia: by_article = aggrega per codice articolo, by_customer_order_line = per riga ordine cliente">Planning mode</th>
                    <th className="text-center py-2 pr-4 font-medium" title="Prerequisito stock policy: attiva solo per articoli by_article con gestione scorte abilitata">Gestione scorte</th>
                    <th className="text-left py-2 pr-2 font-medium" title="Stock policy defaults V1 — Stock mesi / Trigger mesi (solo by_article con gestione scorte attiva)">
                      Stock mesi&nbsp;/&nbsp;Trigger mesi
                    </th>
                    <th className="text-left py-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {famiglie.map((f) => (
                    <RigaFamiglia key={f.code} famiglia={f} onToggled={handleToggled} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
