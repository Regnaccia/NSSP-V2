/**
 * Surface Produzione — tabella gestione famiglie articolo (TASK-V2-025, TASK-V2-026).
 *
 * Consuma:
 *   GET   /api/produzione/famiglie/catalog  — tutte le famiglie + is_active + n_articoli
 *   POST  /api/produzione/famiglie          — crea nuova famiglia
 *   PATCH /api/produzione/famiglie/{code}/active — toggle is_active
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { FamigliaRow } from '@/types/api'

const inputCls =
  'px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'

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

  return (
    <tr className={`border-b last:border-b-0 ${!famiglia.is_active ? 'opacity-50' : ''}`}>
      <td className="py-2.5 pr-6 text-muted-foreground tabular-nums text-sm">
        {famiglia.sort_order ?? '—'}
      </td>
      <td className="py-2.5 pr-6 font-mono text-xs">{famiglia.code}</td>
      <td className="py-2.5 pr-6 font-medium text-sm">{famiglia.label}</td>
      <td className="py-2.5 pr-6 text-right tabular-nums text-sm">
        {famiglia.n_articoli > 0 ? famiglia.n_articoli : (
          <span className="text-muted-foreground">—</span>
        )}
      </td>
      <td className="py-2.5 pr-6">
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
      <td className="py-2.5 pr-6 text-center">
        <input
          type="checkbox"
          checked={famiglia.considera_in_produzione}
          onChange={handleToggleProd}
          disabled={togglingProd}
          className="h-4 w-4 cursor-pointer accent-primary disabled:cursor-wait"
          title={famiglia.considera_in_produzione ? 'Considerata in produzione' : 'Non considerata in produzione'}
        />
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

          {loading && <p className="text-sm text-muted-foreground">Caricamento…</p>}
          {error && <p className="text-sm text-red-600">Impossibile caricare il catalogo famiglie.</p>}

          {!loading && !error && (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b text-xs text-muted-foreground uppercase tracking-wide">
                  <th className="text-left py-2 pr-6 font-medium w-12">Ord.</th>
                  <th className="text-left py-2 pr-6 font-medium">Codice</th>
                  <th className="text-left py-2 pr-6 font-medium">Label</th>
                  <th className="text-right py-2 pr-6 font-medium">Articoli</th>
                  <th className="text-left py-2 pr-6 font-medium">Stato</th>
                  <th className="text-center py-2 pr-6 font-medium">In produzione</th>
                  <th className="text-left py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {famiglie.map((f) => (
                  <RigaFamiglia key={f.code} famiglia={f} onToggled={handleToggled} />
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  )
}
