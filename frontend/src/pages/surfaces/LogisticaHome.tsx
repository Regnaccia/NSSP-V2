/**
 * Surface Logistica — rubrica clienti/destinazioni (DL-UIX-V2-002).
 *
 * Layout a 3 colonne:
 *   1. sinistra  → elenco clienti con filtro
 *   2. centrale  → destinazioni del cliente selezionato
 *   3. destra    → scheda dettaglio + editing nickname
 *
 * Consuma solo i read model Core (mai target sync_* diretti).
 */

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type {
  ClienteItem,
  DestinazioneDetail,
  DestinazioneItem,
  FreshnessResponse,
  SyncSurfaceResponse,
} from '@/types/api'

// ─── Stili condivisi ─────────────────────────────────────────────────────────

const inputCls =
  'w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'
const btnPrimary =
  'py-1.5 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity'
const btnSecondary =
  'py-1.5 px-4 border rounded-md text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50'

// ─── Header: freshness + trigger refresh ─────────────────────────────────────

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
      <span className="font-medium text-foreground">Logistica</span>

      <span className={`px-2 py-0.5 rounded font-medium ${
        anyStale ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
      }`}>
        {anyStale ? 'Dati non aggiornati' : 'Dati aggiornati'}
      </span>

      {lastSync && (
        <span>Ultima sync: {formatDate(lastSync)}</span>
      )}

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

// ─── Stato vuoto guidato ─────────────────────────────────────────────────────

function EmptyHint({ text }: { text: string }) {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  )
}

// ─── Colonna sinistra: lista clienti ─────────────────────────────────────────

function ColonnaClienti({
  clienti,
  loading,
  filter,
  onFilterChange,
  selected,
  onSelect,
}: {
  clienti: ClienteItem[]
  loading: boolean
  filter: string
  onFilterChange: (v: string) => void
  selected: string | null
  onSelect: (codice: string) => void
}) {
  const filtered = clienti.filter(
    (c) =>
      c.ragione_sociale.toLowerCase().includes(filter.toLowerCase()) ||
      c.codice_cli.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="w-64 shrink-0 border-r flex flex-col overflow-hidden">
      {/* Header + filtro */}
      <div className="px-3 py-3 border-b space-y-2 shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Clienti
        </h2>
        <input
          type="search"
          placeholder="Cerca per nome o codice…"
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          className={inputCls}
        />
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <p className="p-4 text-sm text-muted-foreground">Caricamento…</p>
        ) : filtered.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">Nessun cliente</p>
        ) : (
          filtered.map((c) => (
            <button
              key={c.codice_cli}
              onClick={() => onSelect(c.codice_cli)}
              className={`w-full text-left px-3 py-2.5 border-b last:border-b-0 transition-colors ${
                c.codice_cli === selected
                  ? 'bg-primary/10 border-l-2 border-l-primary'
                  : 'hover:bg-muted/50'
              }`}
            >
              <div className="text-sm font-medium truncate">{c.ragione_sociale}</div>
              <div className="text-xs text-muted-foreground">{c.codice_cli}</div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

// ─── Colonna centrale: destinazioni ──────────────────────────────────────────

function ColonnaDestinazioni({
  destinazioni,
  loading,
  clienteSelezionato,
  selected,
  onSelect,
}: {
  destinazioni: DestinazioneItem[]
  loading: boolean
  clienteSelezionato: string | null
  selected: string | null
  onSelect: (codice: string) => void
}) {
  return (
    <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
      <div className="px-3 py-3 border-b shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Destinazioni
        </h2>
      </div>

      {!clienteSelezionato ? (
        <EmptyHint text="Seleziona un cliente" />
      ) : loading ? (
        <p className="p-4 text-sm text-muted-foreground">Caricamento…</p>
      ) : destinazioni.length === 0 ? (
        <EmptyHint text="Nessuna destinazione per questo cliente" />
      ) : (
        <div className="flex-1 overflow-y-auto">
          {destinazioni.map((d) => (
            <button
              key={d.codice_destinazione}
              onClick={() => onSelect(d.codice_destinazione)}
              className={`w-full text-left px-3 py-2.5 border-b last:border-b-0 transition-colors ${
                d.codice_destinazione === selected
                  ? 'bg-primary/10 border-l-2 border-l-primary'
                  : 'hover:bg-muted/50'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-medium truncate">{d.display_label}</span>
                {d.is_primary && (
                  <span className="shrink-0 text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
                    Principale
                  </span>
                )}
              </div>
              {(d.citta || d.provincia) && (
                <div className="text-xs text-muted-foreground">
                  {[d.citta, d.provincia].filter(Boolean).join(' · ')}
                </div>
              )}
              {d.nickname_destinazione && (
                <div className="text-xs text-primary/70 mt-0.5">
                  ✎ {d.nickname_destinazione}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Colonna destra: dettaglio + nickname ─────────────────────────────────────

function RigaInfo({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value}</dd>
    </div>
  )
}

function ColonnaDettaglio({
  destinazioneSelezionata,
  detail,
  loading,
  onNicknameSaved,
}: {
  destinazioneSelezionata: string | null
  detail: DestinazioneDetail | null
  loading: boolean
  onNicknameSaved: () => void
}) {
  const [nicknameDraft, setNicknameDraft] = useState('')
  const [saving, setSaving] = useState(false)

  // Sincronizza il draft quando cambia il dettaglio
  useEffect(() => {
    setNicknameDraft(detail?.nickname_destinazione ?? '')
  }, [detail])

  const handleSave = async () => {
    if (!destinazioneSelezionata) return
    setSaving(true)
    try {
      await apiClient.patch(
        `/logistica/destinazioni/${encodeURIComponent(destinazioneSelezionata)}/nickname`,
        { nickname: nicknameDraft || null }
      )
      toast.success('Nickname salvato')
      onNicknameSaved()
    } catch {
      toast.error('Errore nel salvataggio del nickname')
    } finally {
      setSaving(false)
    }
  }

  const isDirty = nicknameDraft !== (detail?.nickname_destinazione ?? '')

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      {!destinazioneSelezionata ? (
        <EmptyHint text="Seleziona una destinazione" />
      ) : loading || !detail ? (
        <p className="text-sm text-muted-foreground">Caricamento…</p>
      ) : (
        <div className="max-w-lg space-y-6">
          {/* Intestazione */}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold">{detail.display_label}</h2>
              {detail.is_primary && (
                <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
                  Destinazione principale
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{detail.codice_destinazione}</p>
          </div>

          {/* Dati Easy read-only */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
              Dati anagrafici — sola lettura (Easy)
            </h3>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
              <RigaInfo label="Cliente" value={detail.ragione_sociale_cliente} />
              <RigaInfo label="Codice cliente" value={detail.codice_cli} />
              <RigaInfo label="N. progressivo" value={detail.numero_progressivo_cliente} />
              <RigaInfo label="Codice destinazione" value={detail.codice_destinazione} />
              <RigaInfo label="Indirizzo" value={detail.indirizzo} />
              <RigaInfo label="Città" value={detail.citta} />
              <RigaInfo label="Provincia" value={detail.provincia} />
              <RigaInfo label="Nazione" value={detail.nazione_codice} />
              <RigaInfo label="Telefono" value={detail.telefono_1} />
            </dl>
          </section>

          {/* Dato interno configurabile */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b pb-1">
              Configurazione interna
            </h3>
            <div className="space-y-1">
              <label className="text-sm font-medium">
                Nickname destinazione
              </label>
              <p className="text-xs text-muted-foreground">
                Nome interno leggibile — non sovrascrive i dati Easy
              </p>
              <input
                type="text"
                value={nicknameDraft}
                onChange={(e) => setNicknameDraft(e.target.value)}
                placeholder="Es. Sede principale, Hub Nord…"
                className={inputCls}
                disabled={saving}
              />
            </div>
            <div className="flex gap-2 items-center">
              <button
                onClick={handleSave}
                disabled={saving || !isDirty}
                className={btnPrimary}
              >
                {saving ? 'Salvando…' : 'Salva'}
              </button>
              {isDirty && (
                <button
                  onClick={() => setNicknameDraft(detail.nickname_destinazione ?? '')}
                  disabled={saving}
                  className={btnSecondary}
                >
                  Annulla
                </button>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function LogisticaHome() {
  const [clienti, setClienti] = useState<ClienteItem[]>([])
  const [clientiLoading, setClientiLoading] = useState(true)

  const [clientFilter, setClientFilter] = useState('')
  const [selectedCliente, setSelectedCliente] = useState<string | null>(null)

  const [destinazioni, setDestinazioni] = useState<DestinazioneItem[]>([])
  const [destinazioniLoading, setDestinazioniLoading] = useState(false)
  const [selectedDestinazione, setSelectedDestinazione] = useState<string | null>(null)

  const [detail, setDetail] = useState<DestinazioneDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Sync on demand state
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [freshness, setFreshness] = useState<FreshnessResponse | null>(null)

  const loadClienti = () => {
    setClientiLoading(true)
    return apiClient
      .get<ClienteItem[]>('/logistica/clienti')
      .then((r) => setClienti(r.data))
      .catch(() => toast.error('Impossibile caricare i clienti'))
      .finally(() => setClientiLoading(false))
  }

  const loadFreshness = () =>
    apiClient
      .get<FreshnessResponse>('/sync/freshness/logistica')
      .then((r) => setFreshness(r.data))
      .catch(() => {})  // freshness non bloccante

  const handleRefresh = async () => {
    setSyncStatus('syncing')
    try {
      const { data } = await apiClient.post<SyncSurfaceResponse>('/sync/surface/logistica')
      const allOk = data.results.every(r => r.status === 'success')
      if (allOk) {
        setSyncStatus('success')
        toast.success('Dati aggiornati da Easy')
      } else {
        setSyncStatus('error')
        const failed = data.results.filter(r => r.status !== 'success')
        toast.error(`Sync parzialmente fallita: ${failed.map(r => r.entity_code).join(', ')}`)
      }
      // Ricarica clienti e freshness dopo sync
      await Promise.all([loadClienti(), loadFreshness()])
    } catch (err: unknown) {
      setSyncStatus('error')
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      if (detail?.includes('409') || (err as { response?: { status?: number } })?.response?.status === 409) {
        toast.error('Sync già in esecuzione, attendere')
      } else if ((err as { response?: { status?: number } })?.response?.status === 503) {
        toast.error('Easy non configurato — sync non disponibile')
      } else {
        toast.error(detail ?? 'Errore durante la sincronizzazione')
      }
    }
  }

  // Carica clienti e freshness al mount
  useEffect(() => {
    loadClienti()
    loadFreshness()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Carica destinazioni quando cambia cliente selezionato
  useEffect(() => {
    setSelectedDestinazione(null)
    setDetail(null)
    if (!selectedCliente) {
      setDestinazioni([])
      return
    }
    setDestinazioniLoading(true)
    apiClient
      .get<DestinazioneItem[]>(`/logistica/clienti/${encodeURIComponent(selectedCliente)}/destinazioni`)
      .then((r) => setDestinazioni(r.data))
      .catch(() => toast.error('Impossibile caricare le destinazioni'))
      .finally(() => setDestinazioniLoading(false))
  }, [selectedCliente])

  // Carica dettaglio quando cambia destinazione selezionata
  useEffect(() => {
    setDetail(null)
    if (!selectedDestinazione) return
    setDetailLoading(true)
    apiClient
      .get<DestinazioneDetail>(`/logistica/destinazioni/${encodeURIComponent(selectedDestinazione)}`)
      .then((r) => setDetail(r.data))
      .catch(() => toast.error('Impossibile caricare il dettaglio'))
      .finally(() => setDetailLoading(false))
  }, [selectedDestinazione])

  // Ricarica il dettaglio dopo salvataggio nickname (aggiorna anche la riga nella lista)
  const handleNicknameSaved = () => {
    if (!selectedDestinazione) return
    // Aggiorna dettaglio
    apiClient
      .get<DestinazioneDetail>(`/logistica/destinazioni/${encodeURIComponent(selectedDestinazione)}`)
      .then((r) => setDetail(r.data))
      .catch(() => {})
    // Aggiorna lista destinazioni per riflettere il nuovo display_label
    if (selectedCliente) {
      apiClient
        .get<DestinazioneItem[]>(`/logistica/clienti/${encodeURIComponent(selectedCliente)}/destinazioni`)
        .then((r) => setDestinazioni(r.data))
        .catch(() => {})
    }
  }

  return (
    <div className="flex flex-col h-full">
      <FreshnessBar
        freshness={freshness}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
      />
      <div className="flex flex-1 overflow-hidden">
      <ColonnaClienti
        clienti={clienti}
        loading={clientiLoading}
        filter={clientFilter}
        onFilterChange={setClientFilter}
        selected={selectedCliente}
        onSelect={(codice) => {
          setSelectedCliente((prev) => (prev === codice ? null : codice))
        }}
      />
      <ColonnaDestinazioni
        destinazioni={destinazioni}
        loading={destinazioniLoading}
        clienteSelezionato={selectedCliente}
        selected={selectedDestinazione}
        onSelect={setSelectedDestinazione}
      />
      <ColonnaDettaglio
        destinazioneSelezionata={selectedDestinazione}
        detail={detail}
        loading={detailLoading}
        onNicknameSaved={handleNicknameSaved}
      />
      </div>
    </div>
  )
}
