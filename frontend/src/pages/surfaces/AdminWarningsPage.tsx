/**
 * Surface Admin — Warning Config (TASK-V2-077, TASK-V2-081, DL-ARCH-V2-029).
 *
 * Permette all'amministratore di governare la visibilita dei warning per area/reparto.
 * Un tipo warning esiste una sola volta (modulo canonico Warnings);
 * la configurazione determina in quali aree operative il warning e visibile.
 *
 * La surface Warnings e un punto trasversale e non dipende da questa configurazione
 * per esistere — mostra sempre tutti i warning canonici.
 *
 * Endpoint:
 *   GET /api/admin/warnings/config
 *   PUT /api/admin/warnings/config/{warning_type}
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { WarningTypeConfigItem } from '@/types/api'

// ─── Costanti frontend ────────────────────────────────────────────────────────

/** Aree/reparti operativi V1 — rispecchia KNOWN_AREAS del backend */
const KNOWN_AREAS = ['magazzino', 'produzione', 'logistica'] as const
type KnownArea = typeof KNOWN_AREAS[number]

const AREA_LABELS: Record<KnownArea, string> = {
  magazzino: 'Magazzino',
  produzione: 'Produzione',
  logistica: 'Logistica',
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

const btnPrimary =
  'py-1.5 px-3 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:opacity-90 disabled:opacity-50 transition-opacity'
const btnSecondary =
  'py-1.5 px-3 border rounded-md text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50'

// ─── Pannello configurazione per un tipo warning ───────────────────────────────

function WarningTypePanel({
  config,
  onSaved,
}: {
  config: WarningTypeConfigItem
  onSaved: (updated: WarningTypeConfigItem) => void
}) {
  const [selected, setSelected] = useState<string[]>(
    config.visible_to_areas.filter((a) => (KNOWN_AREAS as readonly string[]).includes(a))
  )
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  const toggle = (area: string) => {
    setSelected((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    )
    setDirty(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const { data } = await apiClient.put<WarningTypeConfigItem>(
        `/admin/warnings/config/${config.warning_type}`,
        { visible_to_areas: selected }
      )
      onSaved(data)
      setDirty(false)
      toast.success(`Visibilità di ${config.warning_type} aggiornata`)
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel salvataggio'))
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setSelected(config.visible_to_areas.filter((a) => (KNOWN_AREAS as readonly string[]).includes(a)))
    setDirty(false)
  }

  return (
    <div className="border rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold font-mono">{config.warning_type}</p>
          {config.is_default ? (
            <p className="text-xs text-muted-foreground mt-0.5">Default di sistema — non ancora personalizzato</p>
          ) : (
            <p className="text-xs text-muted-foreground mt-0.5">
              Modificato il{' '}
              {config.updated_at
                ? new Date(config.updated_at).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' })
                : '—'}
            </p>
          )}
        </div>
        {config.is_default && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium shrink-0">
            default
          </span>
        )}
      </div>

      {/* Checkboxes area */}
      <div>
        <p className="text-xs text-muted-foreground mb-2">Visibile nelle aree:</p>
        <div className="flex flex-wrap gap-3">
          {KNOWN_AREAS.map((area) => (
            <label key={area} className="flex items-center gap-1.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={selected.includes(area)}
                onChange={() => toggle(area)}
                disabled={saving}
                className="rounded"
              />
              <span className="text-sm">{AREA_LABELS[area]}</span>
            </label>
          ))}
        </div>
        <p className="text-[10px] text-muted-foreground mt-2">
          La surface <strong>Avvertimenti</strong> mostra sempre tutti i warning indipendentemente da questa configurazione.
        </p>
      </div>

      {/* Azioni */}
      {dirty && (
        <div className="flex items-center gap-2 pt-1">
          <button onClick={handleSave} disabled={saving} className={btnPrimary}>
            {saving ? 'Salvataggio…' : 'Salva'}
          </button>
          <button onClick={handleReset} disabled={saving} className={btnSecondary}>
            Annulla
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function AdminWarningsPage() {
  const [configs, setConfigs] = useState<WarningTypeConfigItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient
      .get<WarningTypeConfigItem[]>('/admin/warnings/config')
      .then((r) => setConfigs(r.data))
      .catch(() => toast.error('Impossibile caricare la configurazione warning'))
      .finally(() => setLoading(false))
  }, [])

  const handleSaved = (updated: WarningTypeConfigItem) => {
    setConfigs((prev) =>
      prev.map((c) => (c.warning_type === updated.warning_type ? updated : c))
    )
  }

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Warning — Visibilità per Area</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configura in quali aree operative ogni tipo di warning è visibile (badge, indicatori).
          La surface <strong>Avvertimenti</strong> è sempre accessibile e mostra tutti i warning.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Caricamento…</p>
      ) : configs.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nessun tipo warning configurabile.</p>
      ) : (
        <div className="space-y-3">
          {configs.map((c) => (
            <WarningTypePanel key={c.warning_type} config={c} onSaved={handleSaved} />
          ))}
        </div>
      )}
    </main>
  )
}
