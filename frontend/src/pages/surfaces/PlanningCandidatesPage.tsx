/**
 * Surface Produzione — Planning Candidates V2 (TASK-V2-065, TASK-V2-071, TASK-V2-072,
 * TASK-V2-075, DL-ARCH-V2-025, DL-ARCH-V2-026, DL-ARCH-V2-027, DL-ARCH-V2-028).
 *
 * Vista operativa con branching reale tra:
 * - planning_mode = by_article  → logica aggregata per articolo (V1)
 * - planning_mode = by_customer_order_line → logica per riga ordine cliente (V2)
 *
 * Toolbar:
 * - ricerca per codice articolo (normalizzata DL-UIX-V2-004)
 * - ricerca per descrizione (testo libero)
 * - filtro famiglia
 * - toggle "Solo perimetro produzione" basato su effective_considera_in_produzione (DL-ARCH-V2-026)
 * - pulsante "Aggiorna" → POST /sync/surface/produzione (DL-ARCH-V2-022)
 *
 * Ordinamento iniziale: required_qty_minimum decrescente (UIX_SPEC_PLANNING_CANDIDATES).
 * La logica di candidatura e applicata nel Core backend — la UI consuma esiti.
 *
 * Colonne TASK-V2-075:
 * - "Motivo" → reason_text esplicito (DL-ARCH-V2-028 §4)
 * - misura → inline nel Codice (DL-ARCH-V2-028 §3)
 * - Descrizione by_customer_order_line → order_line_description come primaria (via display_label backend)
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { PlanningCandidateItem, PlanningMode, SyncSurfaceResponse } from '@/types/api'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type LoadStatus = 'loading' | 'idle' | 'error'
type SyncStatus = 'idle' | 'syncing' | 'success' | 'error'
/** Filtro driver: Tutti / Solo fabbisogno cliente / Solo scorta (TASK-V2-102) */
type DriverFilter = 'tutti' | 'fabbisogno' | 'scorta'

/** Chiavi di ordinamento semantiche — indipendenti dallo shape del ramo */
type SortKey =
  | 'famiglia_label'
  | 'demand'
  | 'availability'
  | 'supply'
  | 'coverage'
  | 'required_qty_minimum'
type SortDir = 'asc' | 'desc'

// ─── Utility ──────────────────────────────────────────────────────────────────

function fmtQty(val: string | null): string {
  if (val == null) return '—'
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 3 })
}

/** Normalizzazione codice articolo (DL-UIX-V2-004): . → x, X varianti → x */
function normalizeCodice(input: string): string {
  return input.trim().replace(/\s*[xX]\s*/g, 'x').replace(/\./g, 'x').toLowerCase()
}

function matchesCodice(item: PlanningCandidateItem, raw: string): boolean {
  if (!raw.trim()) return true
  return item.article_code.toLowerCase().includes(normalizeCodice(raw))
}

function matchesDesc(item: PlanningCandidateItem, raw: string): boolean {
  if (!raw.trim()) return true
  const needle = raw.trim().toLowerCase()
  return item.display_label.toLowerCase().includes(needle)
}

/** Domanda unificata: per-riga (by_col) o aggregata (by_article) */
function resolveDemand(item: PlanningCandidateItem): number {
  return parseFloat(item.line_open_demand_qty ?? item.customer_open_demand_qty ?? '0')
}

/** Supply unificata: collegata alla riga (by_col) o aggregata per articolo (by_article) */
function resolveSupply(item: PlanningCandidateItem): number {
  return parseFloat(item.linked_incoming_supply_qty ?? item.incoming_supply_qty ?? '0')
}

/** Copertura unificata: line_future_coverage (by_col) o future_availability (by_article) */
function resolveCoverage(item: PlanningCandidateItem): number {
  return parseFloat(item.line_future_coverage_qty ?? item.future_availability_qty ?? '0')
}

function cmpItems(
  a: PlanningCandidateItem,
  b: PlanningCandidateItem,
  key: SortKey,
  dir: SortDir,
): number {
  let av: number | string
  let bv: number | string

  switch (key) {
    case 'famiglia_label':
      av = (a.famiglia_label ?? '').toLowerCase()
      bv = (b.famiglia_label ?? '').toLowerCase()
      break
    case 'demand':
      av = resolveDemand(a)
      bv = resolveDemand(b)
      break
    case 'availability':
      av = parseFloat(a.availability_qty ?? '0')
      bv = parseFloat(b.availability_qty ?? '0')
      break
    case 'supply':
      av = resolveSupply(a)
      bv = resolveSupply(b)
      break
    case 'coverage':
      av = resolveCoverage(a)
      bv = resolveCoverage(b)
      break
    case 'required_qty_minimum':
      av = parseFloat(a.required_qty_minimum)
      bv = parseFloat(b.required_qty_minimum)
      break
    default:
      return 0
  }

  if (av < bv) return dir === 'asc' ? -1 : 1
  if (av > bv) return dir === 'asc' ? 1 : -1
  return 0
}

// ─── Badge reason (DL-ARCH-V2-028 §4) ────────────────────────────────────────

/**
 * Badge visivo per il reason_code (DL-ARCH-V2-028 §4).
 * Mostra reason_text — il reason_code determina il colore.
 */
function ReasonBadge({ reasonCode, reasonText }: { reasonCode: string; reasonText: string }) {
  const cls =
    reasonCode === 'future_availability_negative'
      ? 'bg-amber-50 text-amber-700 border border-amber-200'
      : reasonCode === 'line_demand_uncovered'
      ? 'bg-rose-50 text-rose-700 border border-rose-200'
      : 'bg-muted text-muted-foreground'
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cls}`}>
      {reasonText}
    </span>
  )
}

// ─── Badge planning_mode ───────────────────────────────────────────────────────

function PlanningModeBadge({ mode }: { mode: PlanningMode | null }) {
  if (mode === 'by_customer_order_line') {
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-700 whitespace-nowrap">
        per riga
      </span>
    )
  }
  if (mode === 'by_article') {
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 whitespace-nowrap">
        articolo
      </span>
    )
  }
  return <span className="text-muted-foreground/50 italic text-xs">—</span>
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
      <span className="font-medium text-foreground">Planning Candidates</span>

      {loadStatus === 'idle' && (
        <span className={`px-2 py-0.5 rounded font-medium ${
          totalCount > 0 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
        }`}>
          {totalCount > 0
            ? `${shownCount === totalCount ? totalCount : `${shownCount} / ${totalCount}`} candidat${totalCount === 1 ? 'o' : 'i'}`
            : 'Nessun candidate'}
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
          {syncStatus === 'syncing'
            ? 'Aggiornamento dati…'
            : loadStatus === 'loading'
            ? 'Caricamento…'
            : 'Aggiorna dati'}
        </button>
      </div>
    </div>
  )
}

// ─── Filtri ───────────────────────────────────────────────────────────────────

const inputCls =
  'border rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring'

function FiltriBar({
  filterCodice,
  onFilterCodiceChange,
  filterDesc,
  onFilterDescChange,
  famiglie,
  famigliaFilter,
  onFamigliaChange,
  soloInProduzione,
  onSoloInProduzioneChange,
}: {
  filterCodice: string
  onFilterCodiceChange: (v: string) => void
  filterDesc: string
  onFilterDescChange: (v: string) => void
  famiglie: string[]
  famigliaFilter: string
  onFamigliaChange: (v: string) => void
  soloInProduzione: boolean
  onSoloInProduzioneChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0 flex-wrap">
      <label className="flex items-center gap-1.5 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={soloInProduzione}
          onChange={(e) => onSoloInProduzioneChange(e.target.checked)}
          className="rounded"
        />
        <span className="text-xs text-muted-foreground">Solo perimetro produzione</span>
      </label>

      <div className="h-4 border-l" />

      <input
        type="search"
        placeholder="Codice…"
        value={filterCodice}
        onChange={(e) => onFilterCodiceChange(e.target.value)}
        className={inputCls}
      />
      <input
        type="search"
        placeholder="Descrizione…"
        value={filterDesc}
        onChange={(e) => onFilterDescChange(e.target.value)}
        className={inputCls}
      />

      {famiglie.length > 0 && (
        <select
          value={famigliaFilter}
          onChange={(e) => onFamigliaChange(e.target.value)}
          className={inputCls}
        >
          <option value="">Tutte le famiglie</option>
          {famiglie.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      )}
    </div>
  )
}

// ─── Driver filter bar (TASK-V2-102) ─────────────────────────────────────────

const driverOptions: { value: DriverFilter; label: string }[] = [
  { value: 'tutti', label: 'Tutti' },
  { value: 'fabbisogno', label: 'Solo fabbisogno cliente' },
  { value: 'scorta', label: 'Solo scorta' },
]

function DriverFilterBar({
  driverFilter,
  onDriverFilterChange,
  soloEntroHorizon,
  onSoloEntroHorizonChange,
  horizonDays,
  onHorizonDaysChange,
}: {
  driverFilter: DriverFilter
  onDriverFilterChange: (v: DriverFilter) => void
  soloEntroHorizon: boolean
  onSoloEntroHorizonChange: (v: boolean) => void
  horizonDays: number
  onHorizonDaysChange: (v: number) => void
}) {
  const horizonControlDisabled = driverFilter === 'scorta'

  return (
    <div className="flex items-center gap-3 px-4 py-1.5 border-b bg-muted/20 shrink-0 flex-wrap">
      <div className="flex items-center rounded-md border overflow-hidden text-xs font-medium">
        {driverOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onDriverFilterChange(opt.value)}
            className={`px-3 py-1 transition-colors ${
              driverFilter === opt.value
                ? 'bg-foreground text-background'
                : 'hover:bg-muted'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="h-4 border-l" />

      <label className="flex items-center gap-1.5 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={soloEntroHorizon}
          onChange={(e) => onSoloEntroHorizonChange(e.target.checked)}
          disabled={horizonControlDisabled}
          className="rounded"
        />
        <span className={`text-xs ${horizonControlDisabled ? 'text-muted-foreground/50' : 'text-muted-foreground'}`}>
          Entro
        </span>
      </label>
      <input
        type="number"
        min={1}
        max={3650}
        value={horizonDays}
        onChange={(e) => {
          const v = parseInt(e.target.value, 10)
          if (!isNaN(v) && v >= 1) onHorizonDaysChange(v)
        }}
        disabled={!soloEntroHorizon || horizonControlDisabled}
        className="border rounded-md px-2 py-1 text-xs w-16 text-center focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-40"
      />
      <span className={`text-xs ${horizonControlDisabled ? 'text-muted-foreground/50' : 'text-muted-foreground'}`}>
        giorni
      </span>
    </div>
  )
}

// ─── Tabella ──────────────────────────────────────────────────────────────────

const thBase =
  'px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b select-none'
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
      className={`${thBase} cursor-pointer hover:text-foreground transition-colors ${
        align === 'right' ? 'text-right' : ''
      }`}
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
      <p className="text-sm">Nessun articolo richiede nuova attenzione produttiva.</p>
      {soloInProduzione && (
        <p className="text-xs mt-1">
          Tutti gli articoli nel perimetro produzione sono coperti dalla supply in corso.
        </p>
      )}
    </div>
  )
}

function TabellaFiltroVuota() {
  return (
    <div className="flex items-center justify-center flex-1 p-12 text-muted-foreground text-sm">
      Nessun candidate corrisponde ai filtri attivi.
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

function TabellaCandidates({
  items,
  sortKey,
  sortDir,
  onSort,
}: {
  items: PlanningCandidateItem[]
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
            <Th
              label="Famiglia"
              sortKey="famiglia_label"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
            />
            <th className={thBase}>Mode</th>
            <th className={thBase}>Motivo</th>
            <th className={thBase}>Ordine / Riga</th>
            <Th
              label="Domanda"
              sortKey="demand"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
              align="right"
            />
            <Th
              label="Dispon. attuale"
              sortKey="availability"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
              align="right"
            />
            <Th
              label="Supply"
              sortKey="supply"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
              align="right"
            />
            <Th
              label="Copertura"
              sortKey="coverage"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
              align="right"
            />
            <Th
              label="Fabbisogno min."
              sortKey="required_qty_minimum"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
              align="right"
            />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const isByCol = item.planning_mode === 'by_customer_order_line'
            const coverageNeg = resolveCoverage(item) < 0

            // Chiave riga stabile per entrambe le modalita
            const rowKey = `${item.article_code}-${item.order_reference ?? ''}-${item.line_reference ?? ''}`

            // Valori unificati per le colonne condivise
            const demandVal = isByCol ? item.line_open_demand_qty : item.customer_open_demand_qty
            const supplyVal = isByCol ? item.linked_incoming_supply_qty : item.incoming_supply_qty
            const coverageVal = isByCol ? item.line_future_coverage_qty : item.future_availability_qty

            return (
              <tr
                key={rowKey}
                className="border-b last:border-b-0 hover:bg-muted/30 transition-colors"
              >
                <td className={tdCls}>
                  <div className="flex flex-col gap-0.5">
                    <span className="font-mono text-xs">{item.article_code}</span>
                    {item.misura && (
                      <span className="text-[10px] text-muted-foreground">{item.misura}</span>
                    )}
                  </div>
                </td>
                <td className={tdCls}>
                  <span className="text-foreground">{item.display_label}</span>
                </td>
                <td className={tdCls}>
                  {item.famiglia_label ? (
                    <span className="text-muted-foreground">{item.famiglia_label}</span>
                  ) : (
                    <span className="text-muted-foreground/50 italic">—</span>
                  )}
                </td>
                <td className={tdCls}>
                  <PlanningModeBadge mode={item.planning_mode} />
                </td>
                <td className={tdCls}>
                  <ReasonBadge reasonCode={item.reason_code} reasonText={item.reason_text} />
                </td>
                <td className={tdCls}>
                  {isByCol && item.order_reference != null ? (
                    <span className="font-mono text-xs text-muted-foreground">
                      {item.order_reference}
                      {item.line_reference != null && (
                        <span className="text-muted-foreground/60"> / {item.line_reference}</span>
                      )}
                    </span>
                  ) : (
                    <span className="text-muted-foreground/50 italic">—</span>
                  )}
                </td>
                <td className={tdNumCls}>{fmtQty(demandVal)}</td>
                {/* Disponibilita attuale: rilevante solo per by_article */}
                <td className={tdNumCls}>{fmtQty(item.availability_qty)}</td>
                <td className={tdNumCls}>{fmtQty(supplyVal)}</td>
                <td className={`${tdNumCls} ${coverageNeg ? 'text-red-600 font-semibold' : ''}`}>
                  {fmtQty(coverageVal)}
                </td>
                <td className={`${tdNumCls} font-semibold`}>
                  {fmtQty(item.required_qty_minimum)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function PlanningCandidatesPage() {
  const [items, setItems] = useState<PlanningCandidateItem[]>([])
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')

  // Filtri
  const [soloInProduzione, setSoloInProduzione] = useState(true)
  const [filterCodice, setFilterCodice] = useState('')
  const [filterDesc, setFilterDesc] = useState('')
  const [famigliaFilter, setFamigliaFilter] = useState('')
  // Filtri driver + horizon (TASK-V2-102)
  const [driverFilter, setDriverFilter] = useState<DriverFilter>('tutti')
  const [soloEntroHorizon, setSoloEntroHorizon] = useState(false)
  const [horizonDays, setHorizonDays] = useState(30)

  // Ordinamento — default: required_qty_minimum desc (UIX_SPEC_PLANNING_CANDIDATES)
  const [sortKey, setSortKey] = useState<SortKey>('required_qty_minimum')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const horizonDaysRef = useRef(horizonDays)
  horizonDaysRef.current = horizonDays

  const loadCandidates = () => {
    setLoadStatus('loading')
    return apiClient
      .get<PlanningCandidateItem[]>('/produzione/planning-candidates', {
        params: { horizon_days: horizonDaysRef.current },
      })
      .then((r) => {
        setItems(r.data)
        setLoadStatus('idle')
      })
      .catch(() => setLoadStatus('error'))
  }

  useEffect(() => {
    loadCandidates()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Ri-fetcha quando horizonDays cambia (debounced 600ms)
  useEffect(() => {
    const t = setTimeout(() => loadCandidates(), 600)
    return () => clearTimeout(t)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [horizonDays])

  /**
   * Refresh semantico backend (DL-ARCH-V2-022).
   *
   * POST /sync/surface/produzione esegue la chain completa:
   * sync articoli + mag_reale + righe_ordine_cliente + produzioni_attive
   * + rebuild inventory + customer_set_aside + commitments + availability.
   *
   * Al termine ricarica la lista planning candidates.
   */
  const handleRefresh = async () => {
    setSyncStatus('syncing')
    try {
      const { data } = await apiClient.post<SyncSurfaceResponse>('/sync/surface/produzione')
      const allOk = data.results.every((r) => r.status === 'success')
      if (allOk) {
        setSyncStatus('success')
        toast.success('Dati aggiornati da Easy')
      } else {
        setSyncStatus('error')
        const failed = data.results.filter((r) => r.status !== 'success')
        toast.error(`Refresh parzialmente fallito: ${failed.map((r) => r.entity_code).join(', ')}`)
      }
      await loadCandidates()
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
    const labels = items.map((i) => i.famiglia_label).filter((l): l is string => l != null)
    return [...new Set(labels)].sort()
  }, [items])

  const filtered = useMemo(() => {
    return items
      .filter((i) => {
        if (!soloInProduzione) return true
        // Usa effective_considera_in_produzione (DL-ARCH-V2-026):
        // - true → includi
        // - false o null → escludi dal perimetro produzione
        return i.effective_considera_in_produzione === true
      })
      .filter((i) => matchesCodice(i, filterCodice))
      .filter((i) => matchesDesc(i, filterDesc))
      .filter((i) => !famigliaFilter || i.famiglia_label === famigliaFilter)
      .filter((i) => {
        // Filtro driver (TASK-V2-105): usa primary_driver univoco del candidate
        if (driverFilter === 'fabbisogno') {
          return i.primary_driver === 'customer'
        }
        if (driverFilter === 'scorta') {
          return i.primary_driver === 'stock'
        }
        return true
      })
      .filter((i) => {
        // Filtro customer horizon: usa is_within_customer_horizon calcolato dal server con horizon_days
        if (driverFilter === 'scorta') return true
        if (!soloEntroHorizon) return true
        return i.is_within_customer_horizon === true
      })
  }, [items, soloInProduzione, filterCodice, filterDesc, famigliaFilter, driverFilter, soloEntroHorizon])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => cmpItems(a, b, sortKey, sortDir))
  }, [filtered, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'required_qty_minimum' ? 'desc' : 'asc')
    }
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        totalCount={filtered.length}
        shownCount={sorted.length}
        loadStatus={loadStatus}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
      />

      <FiltriBar
        filterCodice={filterCodice}
        onFilterCodiceChange={setFilterCodice}
        filterDesc={filterDesc}
        onFilterDescChange={setFilterDesc}
        famiglie={famiglie}
        famigliaFilter={famigliaFilter}
        onFamigliaChange={setFamigliaFilter}
        soloInProduzione={soloInProduzione}
        onSoloInProduzioneChange={setSoloInProduzione}
      />

      <DriverFilterBar
        driverFilter={driverFilter}
        onDriverFilterChange={(v) => {
          setDriverFilter(v)
          if (v === 'scorta') {
            setSoloEntroHorizon(false)
          } else if (v === 'fabbisogno') {
            setSoloEntroHorizon(true)
          }
        }}
        soloEntroHorizon={soloEntroHorizon}
        onSoloEntroHorizonChange={setSoloEntroHorizon}
        horizonDays={horizonDays}
        onHorizonDaysChange={setHorizonDays}
      />

      {(loadStatus === 'loading' || syncStatus === 'syncing') && (
        <div className="flex items-center justify-center flex-1 p-12 text-muted-foreground text-sm">
          {syncStatus === 'syncing' ? 'Aggiornamento dati da Easy…' : 'Caricamento…'}
        </div>
      )}
      {loadStatus === 'error' && syncStatus !== 'syncing' && <TabellaErrore />}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && filtered.length === 0 && (
        <TabellaVuota soloInProduzione={soloInProduzione} />
      )}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && filtered.length > 0 && sorted.length === 0 && (
        <TabellaFiltroVuota />
      )}
      {loadStatus === 'idle' && syncStatus !== 'syncing' && sorted.length > 0 && (
        <TabellaCandidates
          items={sorted}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={handleSort}
        />
      )}
    </div>
  )
}
