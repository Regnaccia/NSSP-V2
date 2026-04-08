/**
 * Surface Produzione — browser produzioni (TASK-V2-031, TASK-V2-032, TASK-V2-033).
 *
 * Layout a 2 colonne (UIX_SPEC_PRODUZIONI.md):
 *   1. sinistra  → lista produzioni aggregate (attive + storiche) con badge bucket/stato
 *   2. destra    → dettaglio produzione con azione forza_completata (TASK-V2-033)
 *
 * Sync on demand: FreshnessBar con trigger POST /sync/surface/produzioni (TASK-V2-032).
 * Consuma solo i read model Core produzioni (mai sync_* diretti).
 * bucket e stato_produzione vengono letti dal backend, mai ricalcolati nel frontend.
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { FreshnessResponse, ProduzioneItem, SyncSurfaceResponse } from '@/types/api'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type SelectionKey = `${number}:${'active' | 'historical'}`
type SyncStatus = 'idle' | 'syncing' | 'success' | 'error'
type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

function toKey(item: ProduzioneItem): SelectionKey {
  return `${item.id_dettaglio}:${item.bucket}`
}

// ─── FreshnessBar ─────────────────────────────────────────────────────────────

function FreshnessBar({
  freshness,
  syncStatus,
  onRefresh,
}: {
  freshness: FreshnessResponse | null
  syncStatus: SyncStatus
  onRefresh: () => void
}) {
  const isSyncing = syncStatus === 'syncing'

  const formatDate = (iso: string | null) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('it-IT', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
  }

  const lastSync = freshness?.entities.reduce<string | null>((acc, e) => {
    if (!e.last_success_at) return acc
    if (!acc) return e.last_success_at
    return e.last_success_at < acc ? e.last_success_at : acc
  }, null) ?? null

  const anyStale = freshness?.entities.some(e => e.is_stale) ?? true

  return (
    <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/30 text-xs text-muted-foreground shrink-0">
      <span className="font-medium text-foreground">Produzioni</span>

      <span className={`px-2 py-0.5 rounded font-medium ${
        anyStale ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
      }`}>
        {anyStale ? 'Dati non aggiornati' : 'Dati aggiornati'}
      </span>

      {lastSync && <span>Ultima sync: {formatDate(lastSync)}</span>}

      {syncStatus === 'error' && (
        <span className="text-red-600">Sync fallita</span>
      )}

      <div className="ml-auto">
        <button
          onClick={onRefresh}
          disabled={isSyncing}
          className="py-1 px-3 border rounded-md text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
        >
          {isSyncing ? 'Aggiornamento…' : 'Aggiorna dati'}
        </button>
      </div>
    </div>
  )
}

// ─── Badge componenti ─────────────────────────────────────────────────────────

function BucketBadge({ bucket }: { bucket: ProduzioneItem['bucket'] }) {
  return bucket === 'active' ? (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
      Attiva
    </span>
  ) : (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
      Storica
    </span>
  )
}

function StatoBadge({ stato }: { stato: ProduzioneItem['stato_produzione'] }) {
  return stato === 'completata' ? (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
      Completata
    </span>
  ) : (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">
      In corso
    </span>
  )
}

// ─── Colonna sinistra: lista produzioni ──────────────────────────────────────

function ColonnaLista({
  produzioni,
  loading,
  selected,
  onSelect,
}: {
  produzioni: ProduzioneItem[]
  loading: boolean
  selected: SelectionKey | null
  onSelect: (key: SelectionKey) => void
}) {
  return (
    <div className="w-80 shrink-0 border-r flex flex-col overflow-hidden">
      <div className="px-3 py-3 border-b shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Produzioni ({produzioni.length})
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <p className="p-4 text-sm text-muted-foreground">Caricamento…</p>
        ) : produzioni.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">Nessuna produzione</p>
        ) : (
          produzioni.map((p) => {
            const key = toKey(p)
            return (
              <button
                key={key}
                onClick={() => onSelect(key)}
                className={`w-full text-left px-3 py-2.5 border-b last:border-b-0 transition-colors ${
                  key === selected
                    ? 'bg-primary/10 border-l-2 border-l-primary'
                    : 'hover:bg-muted/50'
                }`}
              >
                {/* Riga 1: cliente */}
                <div className="text-xs text-muted-foreground truncate">
                  {p.cliente_ragione_sociale ?? '—'}
                </div>
                {/* Riga 2: articolo */}
                <div className="text-sm font-medium truncate leading-snug">
                  {p.codice_articolo
                    ? <span className="font-mono">{p.codice_articolo}</span>
                    : <span className="italic text-muted-foreground">—</span>
                  }
                  {p.descrizione_articolo && (
                    <span className="ml-1 font-normal text-muted-foreground">
                      {p.descrizione_articolo}
                    </span>
                  )}
                </div>
                {/* Riga 3: documento + badge */}
                <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                  {p.numero_documento && (
                    <span className="text-xs text-muted-foreground font-mono">
                      {p.numero_documento}
                      {p.numero_riga_documento != null && `/${p.numero_riga_documento}`}
                    </span>
                  )}
                  <BucketBadge bucket={p.bucket} />
                  <StatoBadge stato={p.stato_produzione} />
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}

// ─── Colonna destra: dettaglio produzione ─────────────────────────────────────

function RigaInfo({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === '') return null
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{String(value)}</dd>
    </div>
  )
}

function ColonnaDettaglio({
  produzione,
  onToggleForzaCompletata,
}: {
  produzione: ProduzioneItem | null
  onToggleForzaCompletata: (item: ProduzioneItem) => Promise<void>
}) {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  // Resetta feedback al cambio di produzione selezionata
  useEffect(() => {
    setSaveStatus('idle')
  }, [produzione && toKey(produzione)])

  const handleToggle = async () => {
    if (!produzione) return
    setSaveStatus('saving')
    try {
      await onToggleForzaCompletata(produzione)
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2500)
    } catch {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3500)
    }
  }

  if (!produzione) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Seleziona una produzione</p>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="max-w-lg space-y-6">
        {/* Intestazione */}
        <div>
          <h2 className="text-lg font-semibold">
            {produzione.codice_articolo ?? '—'}
          </h2>
          {produzione.descrizione_articolo && (
            <p className="text-sm text-muted-foreground">{produzione.descrizione_articolo}</p>
          )}
          <p className="text-xs font-mono text-muted-foreground mt-0.5">
            id_dettaglio: {produzione.id_dettaglio}
          </p>
        </div>

        {/* Stato e classificazione */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Stato e classificazione
          </h3>
          <div className="flex items-center gap-3 flex-wrap">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Bucket</p>
              <BucketBadge bucket={produzione.bucket} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Stato produzione</p>
              <StatoBadge stato={produzione.stato_produzione} />
            </div>
          </div>
        </section>

        {/* Override forza_completata — azione operativa (TASK-V2-033) */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Override interno V2
          </h3>
          <div className="rounded-md border p-4 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium">Forza completata</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Segna la produzione come completata indipendentemente dalle quantità Easy.
                  Non modifica i dati sorgente.
                </p>
              </div>
              <button
                onClick={handleToggle}
                disabled={saveStatus === 'saving'}
                className={`shrink-0 py-1.5 px-3 rounded-md text-xs font-medium border transition-colors disabled:opacity-50 ${
                  produzione.forza_completata
                    ? 'bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100'
                    : 'bg-muted border-border text-foreground hover:bg-muted/80'
                }`}
              >
                {saveStatus === 'saving'
                  ? 'Salvataggio…'
                  : produzione.forza_completata
                    ? 'Rimuovi override'
                    : 'Forza completata'}
              </button>
            </div>

            {produzione.forza_completata && (
              <div className="flex items-center gap-1.5">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700">
                  Override attivo
                </span>
                <span className="text-xs text-muted-foreground">
                  — stato_produzione = completata per override interno
                </span>
              </div>
            )}

            {saveStatus === 'saved' && (
              <p className="text-xs text-green-600">Salvato</p>
            )}
            {saveStatus === 'error' && (
              <p className="text-xs text-red-600">Errore durante il salvataggio</p>
            )}
          </div>
        </section>

        {/* Dati documento */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Documento — sola lettura (Easy)
          </h3>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
            <RigaInfo label="Cliente" value={produzione.cliente_ragione_sociale} />
            <RigaInfo label="Numero documento" value={produzione.numero_documento} />
            <RigaInfo label="Riga documento" value={produzione.numero_riga_documento} />
          </dl>
        </section>

        {/* Quantità */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Quantità — sola lettura (Easy)
          </h3>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
            <RigaInfo label="Qtà ordinata" value={produzione.quantita_ordinata} />
            <RigaInfo label="Qtà prodotta" value={produzione.quantita_prodotta} />
          </dl>
        </section>
      </div>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function ProduzioniPage() {
  const [produzioni, setProduzioni] = useState<ProduzioneItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<SelectionKey | null>(null)
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [freshness, setFreshness] = useState<FreshnessResponse | null>(null)

  const loadProduzioni = () => {
    setLoading(true)
    return apiClient
      .get<ProduzioneItem[]>('/produzione/produzioni')
      .then((r) => setProduzioni(r.data))
      .catch(() => toast.error('Impossibile caricare le produzioni'))
      .finally(() => setLoading(false))
  }

  const loadFreshness = () =>
    apiClient
      .get<FreshnessResponse>('/sync/freshness/produzioni')
      .then((r) => setFreshness(r.data))
      .catch(() => {})

  const handleRefresh = async () => {
    setSyncStatus('syncing')
    try {
      const { data } = await apiClient.post<SyncSurfaceResponse>('/sync/surface/produzioni')
      const allOk = data.results.every(r => r.status === 'success')
      if (allOk) {
        setSyncStatus('success')
        toast.success('Dati produzioni aggiornati da Easy')
      } else {
        setSyncStatus('error')
        const failed = data.results.filter(r => r.status !== 'success')
        toast.error(`Sync parzialmente fallita: ${failed.map(r => r.entity_code).join(', ')}`)
      }
      await Promise.all([loadProduzioni(), loadFreshness()])
    } catch (err: unknown) {
      setSyncStatus('error')
      const resp = (err as { response?: { status?: number; data?: { detail?: string } } })?.response
      if (resp?.status === 409) {
        toast.error('Sync già in esecuzione, attendere')
      } else if (resp?.status === 503) {
        toast.error('Easy non configurato — sync non disponibile')
      } else {
        toast.error(resp?.data?.detail ?? 'Errore durante la sincronizzazione')
      }
    }
  }

  /**
   * Chiama PATCH /produzione/produzioni/{id_dettaglio}/forza-completata
   * e aggiorna il record nella lista con il ProduzioneItem restituito dal backend.
   * Il backend calcola il nuovo stato_produzione — il frontend non lo ricalcola.
   */
  const handleToggleForzaCompletata = async (item: ProduzioneItem) => {
    const { data: updated } = await apiClient.patch<ProduzioneItem>(
      `/produzione/produzioni/${item.id_dettaglio}/forza-completata`,
      { bucket: item.bucket, forza_completata: !item.forza_completata },
    )
    // Sostituisce il record nella lista con il dato aggiornato dal backend
    setProduzioni((prev) =>
      prev.map((p) => (toKey(p) === toKey(updated) ? updated : p))
    )
  }

  useEffect(() => {
    loadProduzioni()
    loadFreshness()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const selectedItem = selected
    ? produzioni.find((p) => toKey(p) === selected) ?? null
    : null

  return (
    <div className="flex flex-col h-full">
      <FreshnessBar
        freshness={freshness}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
      />
      <div className="flex flex-1 overflow-hidden">
        <ColonnaLista
          produzioni={produzioni}
          loading={loading}
          selected={selected}
          onSelect={(key) => setSelected((prev) => (prev === key ? null : key))}
        />
        <ColonnaDettaglio
          produzione={selectedItem}
          onToggleForzaCompletata={handleToggleForzaCompletata}
        />
      </div>
    </div>
  )
}
