/**
 * Surface Produzione — vista criticita articoli (TASK-V2-055, TASK-V2-056, TASK-V2-057,
 * TASK-V2-058, DL-ARCH-V2-023).
 *
 * Lista tabellare di articoli critici (availability_qty < 0).
 *
 * Refinement TASK-V2-056:
 * - perimetro default: solo famiglie con considera_in_produzione = true
 * - filtro per famiglia (client-side)
 * - ordinamento colonne: Famiglia, Giacenza, Appartata, Impegnata, Disponibilita
 *
 * Refinement TASK-V2-057:
 * - toggle "Solo perimetro produzione" (default attivo)
 *
 * Refinement TASK-V2-058:
 * - pulsante "Aggiorna" triggera il refresh semantico backend della surface produzione
 *   (POST /sync/surface/produzione) e ricaricare la lista al termine
 *
 * La logica di criticita e applicata nel Core backend — la UI consuma esiti.
 */

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { CriticitaItem, SyncSurfaceResponse } from '@/types/api'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type LoadStatus = 'loading' | 'idle' | 'error'
type SyncStatus = 'idle' | 'syncing' | 'success' | 'error'
type SortKey = 'famiglia_label' | 'inventory_qty' | 'customer_set_aside_qty' | 'committed_qty' | 'availability_qty'
type SortDir = 'asc' | 'desc'

// ─── Utility ──────────────────────────────────────────────────────────────────

function fmtQty(val: string | null): string {
  if (val == null) return '—'
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 3 })
}

function cmpItems(a: CriticitaItem, b: CriticitaItem, key: SortKey, dir: SortDir): number {
  let av: number | string
  let bv: number | string

  if (key === 'famiglia_label') {
    av = (a.famiglia_label ?? '').toLowerCase()
    bv = (b.famiglia_label ?? '').toLowerCase()
  } else {
    av = parseFloat(a[key] ?? '0')
    bv = parseFloat(b[key] ?? '0')
  }

  if (av < bv) return dir === 'asc' ? -1 : 1
  if (av > bv) return dir === 'asc' ? 1 : -1
  return 0
}

// ─── Header ───────────────────────────────────────────────────────────────────

function PageHeader({
  totalCount,
  shownCount,
  loadStatus,
  syncStatus,
  onRefresh,
}: {
  totalCount: number
  shownCount: number
  loadStatus: LoadStatus
  syncStatus: SyncStatus
  onRefresh: () => void
}) {
  const busy = loadStatus === 'loading' || syncStatus === 'syncing'

  return (
    <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/30 text-xs text-muted-foreground shrink-0">
      <span className="font-medium text-foreground">Criticità articoli</span>

      {loadStatus === 'idle' && (
        <span className={`px-2 py-0.5 rounded font-medium ${
          totalCount > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
        }`}>
          {totalCount > 0
            ? `${shownCount} / ${totalCount} articol${totalCount === 1 ? 'o critico' : 'i critici'}`
            : 'Nessun articolo critico'}
        </span>
      )}

      {loadStatus === 'error' && (
        <span className="px-2 py-0.5 rounded font-medium bg-red-100 text-red-700">
          Errore caricamento
        </span>
      )}

      {syncStatus === 'error' && loadStatus !== 'error' && (
        <span className="text-red-600">Refresh fallito</span>
      )}

      <div className="ml-auto">
        <button
          onClick={onRefresh}
          disabled={busy}
          className="py-1 px-3 border rounded-md text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
        >
          {syncStatus === 'syncing' ? 'Aggiornamento dati…' : loadStatus === 'loading' ? 'Caricamento…' : 'Aggiorna dati'}
        </button>
      </div>
    </div>
  )
}

// ─── Filtri + toggle ──────────────────────────────────────────────────────────

function FiltriBar({
  famiglie,
  famigliaFilter,
  onFamigliaChange,
  soloInProduzione,
  onSoloInProduzioneChange,
}: {
  famiglie: string[]
  famigliaFilter: string
  onFamigliaChange: (v: string) => void
  soloInProduzione: boolean
  onSoloInProduzioneChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center gap-4 px-4 py-2 border-b bg-background shrink-0 flex-wrap">
      <label className="flex items-center gap-1.5 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={soloInProduzione}
          onChange={(e) => onSoloInProduzioneChange(e.target.checked)}
          className="rounded"
        />
        <span className="text-xs text-muted-foreground">Solo perimetro produzione</span>
      </label>

      {famiglie.length > 0 && (
        <>
          <div className="h-4 border-l" />
          <label className="text-xs text-muted-foreground">Famiglia</label>
          <select
            value={famigliaFilter}
            onChange={(e) => onFamigliaChange(e.target.value)}
            className="text-xs border rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tutte le famiglie</option>
            {famiglie.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </>
      )}
    </div>
  )
}

// ─── Tabella ──────────────────────────────────────────────────────────────────

const thBase = 'px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b select-none'
const tdCls = 'px-3 py-2 text-sm'
const tdNumCls = `${tdCls} text-right font-mono tabular-nums`

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-muted-foreground/30">↕</span>
  return <span className="ml-1">{dir === 'asc' ? '↑' : '↓'}</span>
}

function Th({
  label,
  sortKey,
  currentKey,
  dir,
  onSort,
  align,
}: {
  label: string
  sortKey: SortKey
  currentKey: SortKey
  dir: SortDir
  onSort: (k: SortKey) => void
  align?: 'right'
}) {
  const active = currentKey === sortKey
  return (
    <th
      className={`${thBase} cursor-pointer hover:text-foreground transition-colors ${align === 'right' ? 'text-right' : ''}`}
      onClick={() => onSort(sortKey)}
    >
      {label}
      <SortIcon active={active} dir={dir} />
    </th>
  )
}

function TabellaVuota({ soloInProduzione }: { soloInProduzione: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 p-12 text-muted-foreground">
      <p className="text-sm">Nessun articolo critico al momento.</p>
      {soloInProduzione ? (
        <p className="text-xs mt-1">
          La disponibilita di tutti gli articoli nel perimetro produzione e &ge; 0.
        </p>
      ) : (
        <p className="text-xs mt-1">La disponibilita di tutti gli articoli e &ge; 0.</p>
      )}
    </div>
  )
}

function TabellaErrore() {
  return (
    <div className="flex items-center justify-center flex-1 p-12 text-red-600 text-sm">
      Impossibile caricare i dati. Riprovare.
    </div>
  )
}

function TabellaFiltroVuota() {
  return (
    <div className="flex items-center justify-center flex-1 p-12 text-muted-foreground text-sm">
      Nessun articolo critico in questa famiglia.
    </div>
  )
}

function TabellaCriticita({
  items,
  sortKey,
  sortDir,
  onSort,
}: {
  items: CriticitaItem[]
  sortKey: SortKey
  sortDir: SortDir
  onSort: (k: SortKey) => void
}) {
  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-background">
          <tr>
            <th className={thBase}>Codice</th>
            <th className={thBase}>Descrizione</th>
            <Th label="Famiglia" sortKey="famiglia_label" currentKey={sortKey} dir={sortDir} onSort={onSort} />
            <Th label="Giacenza" sortKey="inventory_qty" currentKey={sortKey} dir={sortDir} onSort={onSort} align="right" />
            <Th label="Appartata" sortKey="customer_set_aside_qty" currentKey={sortKey} dir={sortDir} onSort={onSort} align="right" />
            <Th label="Impegnata" sortKey="committed_qty" currentKey={sortKey} dir={sortDir} onSort={onSort} align="right" />
            <Th label="Disponibilita" sortKey="availability_qty" currentKey={sortKey} dir={sortDir} onSort={onSort} align="right" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.article_code} className="border-b last:border-b-0 hover:bg-muted/30 transition-colors">
              <td className={tdCls}>
                <span className="font-mono text-xs">{item.article_code}</span>
              </td>
              <td className={tdCls}>
                <span className="text-foreground">{item.display_label}</span>
              </td>
              <td className={tdCls}>
                {item.famiglia_label
                  ? <span className="text-muted-foreground">{item.famiglia_label}</span>
                  : <span className="text-muted-foreground/50 italic">—</span>
                }
              </td>
              <td className={tdNumCls}>{fmtQty(item.inventory_qty)}</td>
              <td className={tdNumCls}>{fmtQty(item.customer_set_aside_qty)}</td>
              <td className={tdNumCls}>{fmtQty(item.committed_qty)}</td>
              <td className={`${tdNumCls} font-semibold text-red-600`}>
                {fmtQty(item.availability_qty)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function CriticitaPage() {
  const [items, setItems] = useState<CriticitaItem[]>([])
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [soloInProduzione, setSoloInProduzione] = useState(true)
  const [famigliaFilter, setFamigliaFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('availability_qty')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  const loadCriticita = (sip: boolean) => {
    setLoadStatus('loading')
    return apiClient
      .get<CriticitaItem[]>(`/produzione/criticita?solo_in_produzione=${sip}`)
      .then((r) => {
        setItems(r.data)
        setFamigliaFilter('')
        setLoadStatus('idle')
      })
      .catch(() => {
        setLoadStatus('error')
      })
  }

  useEffect(() => {
    loadCriticita(soloInProduzione)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSoloInProduzioneChange = (v: boolean) => {
    setSoloInProduzione(v)
    loadCriticita(v)
  }

  /**
   * Refresh semantico backend (TASK-V2-058, DL-ARCH-V2-022).
   *
   * POST /sync/surface/produzione esegue la chain completa:
   * sync articoli + mag_reale + righe_ordine_cliente + produzioni_attive
   * + rebuild inventory + customer_set_aside + commitments + availability.
   *
   * Al termine ricarica la lista criticita con il perimetro corrente.
   */
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
        toast.error(`Refresh parzialmente fallito: ${failed.map(r => r.entity_code).join(', ')}`)
      }
      await loadCriticita(soloInProduzione)
    } catch (err: unknown) {
      setSyncStatus('error')
      const resp = (err as { response?: { status?: number; data?: { detail?: string } } })?.response
      if (resp?.status === 409) {
        toast.error('Refresh gia in esecuzione, attendere')
      } else if (resp?.status === 503) {
        toast.error('Easy non configurato — refresh non disponibile')
      } else {
        toast.error(resp?.data?.detail ?? 'Errore durante il refresh')
      }
    }
  }

  const famiglie = useMemo(() => {
    const labels = items
      .map((i) => i.famiglia_label)
      .filter((l): l is string => l != null)
    return [...new Set(labels)].sort()
  }, [items])

  const filtered = useMemo(() => {
    if (!famigliaFilter) return items
    return items.filter((i) => i.famiglia_label === famigliaFilter)
  }, [items, famigliaFilter])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => cmpItems(a, b, sortKey, sortDir))
  }, [filtered, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        totalCount={items.length}
        shownCount={sorted.length}
        loadStatus={loadStatus}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
      />

      <FiltriBar
        famiglie={famiglie}
        famigliaFilter={famigliaFilter}
        onFamigliaChange={setFamigliaFilter}
        soloInProduzione={soloInProduzione}
        onSoloInProduzioneChange={handleSoloInProduzioneChange}
      />

      {(loadStatus === 'loading' || syncStatus === 'syncing') && (
        <div className="flex items-center justify-center flex-1 p-12 text-muted-foreground text-sm">
          {syncStatus === 'syncing' ? 'Aggiornamento dati da Easy…' : 'Caricamento…'}
        </div>
      )}
      {loadStatus === 'error' && syncStatus !== 'syncing' && <TabellaErrore />}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && items.length === 0 && (
        <TabellaVuota soloInProduzione={soloInProduzione} />
      )}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && items.length > 0 && sorted.length === 0 && (
        <TabellaFiltroVuota />
      )}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && sorted.length > 0 && (
        <TabellaCriticita
          items={sorted}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={handleSort}
        />
      )}
    </div>
  )
}
