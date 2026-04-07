/**
 * Surface Produzione — browser articoli (TASK-V2-020).
 *
 * Layout a 2 colonne (UIX_SPEC_ARTICOLI.md):
 *   1. sinistra  → lista articoli con ricerca normalizzata (DL-UIX-V2-004)
 *   2. destra    → dettaglio articolo read-only
 *
 * Tutti i dati sono read-only nel primo slice.
 * Consuma solo i read model Core articoli (mai sync_* diretti).
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { ArticoloDetail, ArticoloItem, FamigliaItem, FreshnessResponse, SyncSurfaceResponse } from '@/types/api'

// ─── Normalizzazione ricerca articolo (DL-UIX-V2-004) ────────────────────────
//
// Converte separatori dimensionali alternativi verso il canonico "x".
// Esempi equivalenti: "8.7.40" == "8 x 7 x 40" == "8X7X40" == "8x7x40"

function normalizeSearch(input: string): string {
  return input
    .trim()
    .replace(/\s*[xX]\s*/g, 'x')   // normalizza varianti con spazi intorno a x/X
    .replace(/\./g, 'x')            // converte . in x
    .toLowerCase()
}

function matchesSearch(articolo: ArticoloItem, raw: string): boolean {
  if (!raw.trim()) return true
  const needle = normalizeSearch(raw)
  const codice = articolo.codice_articolo.toLowerCase()
  const desc1 = normalizeSearch(articolo.descrizione_1 ?? '')
  const desc2 = normalizeSearch(articolo.descrizione_2 ?? '')
  return (
    codice.includes(needle) ||
    desc1.includes(needle) ||
    desc2.includes(needle)
  )
}

// ─── Stili condivisi ─────────────────────────────────────────────────────────

const inputCls =
  'w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'

// ─── FreshnessBar ─────────────────────────────────────────────────────────────

type SyncStatus = 'idle' | 'syncing' | 'success' | 'error'

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
      <span className="font-medium text-foreground">Produzione</span>

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

// ─── Colonna sinistra: lista articoli ─────────────────────────────────────────

function ColonnaArticoli({
  articoli,
  loading,
  filter,
  onFilterChange,
  selected,
  onSelect,
}: {
  articoli: ArticoloItem[]
  loading: boolean
  filter: string
  onFilterChange: (v: string) => void
  selected: string | null
  onSelect: (codice: string) => void
}) {
  const filtered = articoli.filter((a) => matchesSearch(a, filter))

  return (
    <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
      {/* Header + ricerca */}
      <div className="px-3 py-3 border-b space-y-2 shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Articoli
        </h2>
        <input
          type="search"
          placeholder="Cerca per codice o descrizione…"
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          className={inputCls}
        />
        {filter.trim() && (
          <p className="text-xs text-muted-foreground">
            {filtered.length} risultat{filtered.length === 1 ? 'o' : 'i'}
          </p>
        )}
      </div>

      {/* Lista scrollabile */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <p className="p-4 text-sm text-muted-foreground">Caricamento…</p>
        ) : filtered.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">Nessun articolo</p>
        ) : (
          filtered.map((a) => (
            <button
              key={a.codice_articolo}
              onClick={() => onSelect(a.codice_articolo)}
              className={`w-full text-left px-3 py-2.5 border-b last:border-b-0 transition-colors ${
                a.codice_articolo === selected
                  ? 'bg-primary/10 border-l-2 border-l-primary'
                  : 'hover:bg-muted/50'
              }`}
            >
              <div className="text-xs font-mono text-muted-foreground">{a.codice_articolo}</div>
              <div className="text-sm font-medium truncate leading-snug">
                {a.descrizione_1 ?? <span className="text-muted-foreground italic">—</span>}
              </div>
              {a.unita_misura_codice && (
                <div className="text-xs text-muted-foreground">{a.unita_misura_codice}</div>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  )
}

// ─── Colonna destra: dettaglio articolo ───────────────────────────────────────

function RigaInfo({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value}</dd>
    </div>
  )
}

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

function ColonnaDettaglio({
  articoloSelezionato,
  detail,
  loading,
  famiglie,
  onFamigliaChange,
}: {
  articoloSelezionato: string | null
  detail: ArticoloDetail | null
  loading: boolean
  famiglie: FamigliaItem[]
  onFamigliaChange: (codice: string, familgiaCode: string | null) => Promise<void>
}) {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  // Resetta il feedback quando cambia articolo
  useEffect(() => {
    setSaveStatus('idle')
  }, [detail?.codice_articolo])

  const handleFamigliaSelect = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (!detail) return
    const newCode = e.target.value || null
    setSaveStatus('saving')
    try {
      await onFamigliaChange(detail.codice_articolo, newCode)
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2500)
    } catch {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3500)
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return null
    try {
      return new Date(iso).toLocaleString('it-IT', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    } catch {
      return iso
    }
  }

  if (!articoloSelezionato) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Seleziona un articolo</p>
      </div>
    )
  }

  if (loading || !detail) {
    return (
      <div className="flex-1 p-6">
        <p className="text-sm text-muted-foreground">Caricamento…</p>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="max-w-lg space-y-6">
        {/* Intestazione */}
        <div>
          <h2 className="text-lg font-semibold">{detail.display_label}</h2>
          <p className="text-sm font-mono text-muted-foreground">{detail.codice_articolo}</p>
        </div>

        {/* Famiglia articolo — dato interno V2 (DL-ARCH-V2-014) */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Classificazione interna
          </h3>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Famiglia articolo</label>
            <select
              value={detail.famiglia_code ?? ''}
              onChange={handleFamigliaSelect}
              disabled={saveStatus === 'saving'}
              className={inputCls}
            >
              <option value="">— nessuna —</option>
              {famiglie.map((f) => (
                <option key={f.code} value={f.code}>
                  {f.label}
                </option>
              ))}
            </select>
            {saveStatus === 'saving' && (
              <p className="text-xs text-muted-foreground">Salvataggio…</p>
            )}
            {saveStatus === 'saved' && (
              <p className="text-xs text-green-600">Salvato</p>
            )}
            {saveStatus === 'error' && (
              <p className="text-xs text-red-600">Errore durante il salvataggio</p>
            )}
          </div>
        </section>

        {/* Dati Easy read-only */}
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
            Dati anagrafici — sola lettura (Easy)
          </h3>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
            <RigaInfo label="Descrizione 1" value={detail.descrizione_1} />
            <RigaInfo label="Descrizione 2" value={detail.descrizione_2} />
            <RigaInfo label="Unità di misura" value={detail.unita_misura_codice} />
            <RigaInfo label="Misura" value={detail.misura_articolo} />
            <RigaInfo label="Categoria 1" value={detail.categoria_articolo_1} />
            <RigaInfo label="Codice immagine" value={detail.codice_immagine} />
            <RigaInfo label="Contenitori magazzino" value={detail.contenitori_magazzino} />
            <RigaInfo label="Materiale grezzo" value={detail.materiale_grezzo_codice} />
            <RigaInfo
              label="Qtà materiale grezzo"
              value={detail.quantita_materiale_grezzo_occorrente}
            />
            <RigaInfo
              label="Qtà scarto materiale"
              value={detail.quantita_materiale_grezzo_scarto}
            />
            <RigaInfo label="Peso (g)" value={detail.peso_grammi} />
            <RigaInfo label="Ultima modifica Easy" value={formatDate(detail.source_modified_at)} />
          </dl>
        </section>
      </div>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function ProduzioneHome() {
  const [articoli, setArticoli] = useState<ArticoloItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<ArticoloDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [famiglie, setFamiglie] = useState<FamigliaItem[]>([])

  // Sync on demand state
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [freshness, setFreshness] = useState<FreshnessResponse | null>(null)

  const loadArticoli = () => {
    setLoading(true)
    return apiClient
      .get<ArticoloItem[]>('/produzione/articoli')
      .then((r) => setArticoli(r.data))
      .catch(() => toast.error('Impossibile caricare gli articoli'))
      .finally(() => setLoading(false))
  }

  const loadFreshness = () =>
    apiClient
      .get<FreshnessResponse>('/sync/freshness/produzione')
      .then((r) => setFreshness(r.data))
      .catch(() => {})  // freshness non bloccante

  const loadFamiglie = () =>
    apiClient
      .get<FamigliaItem[]>('/produzione/famiglie')
      .then((r) => setFamiglie(r.data))
      .catch(() => {})  // famiglie non bloccanti

  const handleFamigliaChange = async (codice: string, familgiaCode: string | null) => {
    await apiClient.patch(`/produzione/articoli/${encodeURIComponent(codice)}/famiglia`, {
      famiglia_code: familgiaCode,
    })
    // Aggiorna il dettaglio corrente senza ricaricare tutta la lista
    setDetail((prev) =>
      prev && prev.codice_articolo === codice
        ? {
            ...prev,
            famiglia_code: familgiaCode,
            famiglia_label: famiglie.find((f) => f.code === familgiaCode)?.label ?? null,
          }
        : prev
    )
  }

  const handleRefresh = async () => {
    setSyncStatus('syncing')
    try {
      const { data } = await apiClient.post<SyncSurfaceResponse>('/sync/surface/produzione')
      const allOk = data.results.every(r => r.status === 'success')
      if (allOk) {
        setSyncStatus('success')
        toast.success('Dati aggiornati da Easy')
      } else {
        setSyncStatus('error')
        const failed = data.results.filter(r => r.status !== 'success')
        toast.error(`Sync parzialmente fallita: ${failed.map(r => r.entity_code).join(', ')}`)
      }
      await Promise.all([loadArticoli(), loadFreshness()])
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

  useEffect(() => {
    loadArticoli()
    loadFreshness()
    loadFamiglie()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setDetail(null)
    if (!selected) return
    setDetailLoading(true)
    apiClient
      .get<ArticoloDetail>(`/produzione/articoli/${encodeURIComponent(selected)}`)
      .then((r) => setDetail(r.data))
      .catch(() => toast.error('Impossibile caricare il dettaglio'))
      .finally(() => setDetailLoading(false))
  }, [selected])

  return (
    <div className="flex flex-col h-full">
      <FreshnessBar
        freshness={freshness}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
      />
      <div className="flex flex-1 overflow-hidden">
        <ColonnaArticoli
          articoli={articoli}
          loading={loading}
          filter={filter}
          onFilterChange={setFilter}
          selected={selected}
          onSelect={(codice) =>
            setSelected((prev) => (prev === codice ? null : codice))
          }
        />
        <ColonnaDettaglio
          articoloSelezionato={selected}
          detail={detail}
          loading={detailLoading}
          famiglie={famiglie}
          onFamigliaChange={handleFamigliaChange}
        />
      </div>
    </div>
  )
}
