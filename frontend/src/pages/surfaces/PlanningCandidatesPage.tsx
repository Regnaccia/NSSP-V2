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
 * - "Motivi" sintetici Cliente/Scorta
 * - colonna misura dedicata
 * - descrizione unificata da description_parts / display_description (TASK-V2-110)
 * - colonna Warnings da active_warnings (TASK-V2-112)
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type {
  ArticoloDetail,
  FamigliaItem,
  PlanningCandidateItem,
  ProposalWorkspaceGenerateResult,
  SyncSurfaceResponse,
} from '@/types/api'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type LoadStatus = 'loading' | 'idle' | 'error'
type SyncStatus = 'idle' | 'syncing' | 'success' | 'error'
/** Filtro driver: Tutti / Solo fabbisogno cliente / Solo scorta (TASK-V2-102) */
type DriverFilter = 'tutti' | 'fabbisogno' | 'scorta'
type TriState = 'null' | 'true' | 'false'

/** Chiavi di ordinamento semantiche — indipendenti dallo shape del ramo */
type SortKey =
  | 'article_code'
  | 'famiglia_label'
  | 'requested_date'
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

function fmtDate(val: string | null): string {
  if (!val) return '—'
  const d = new Date(`${val}T00:00:00`)
  if (isNaN(d.getTime())) return val
  return d.toLocaleDateString('it-IT')
}

function isDateWithinHorizon(val: string | null, horizonDays: number): boolean {
  if (!val) return false
  const delivery = new Date(`${val}T00:00:00`)
  if (isNaN(delivery.getTime())) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const horizon = new Date(today)
  horizon.setDate(horizon.getDate() + horizonDays)
  return delivery <= horizon
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
  const haystack = [item.display_description, item.display_label, ...item.description_parts]
    .filter((s): s is string => Boolean(s))
    .join(' ')
    .toLowerCase()
  return haystack.includes(needle)
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

function resolveRequestedDate(item: PlanningCandidateItem): string | null {
  return item.planning_mode === 'by_customer_order_line'
    ? item.requested_delivery_date
    : item.earliest_customer_delivery_date
}

function resolveDescriptionLines(item: PlanningCandidateItem): string[] {
  const normalizedParts = item.description_parts
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  if (normalizedParts.length > 0) return normalizedParts
  const fallback = (item.display_description || item.display_label).trim()
  return fallback ? [fallback] : ['—']
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
    case 'article_code':
      av = a.article_code.toLowerCase()
      bv = b.article_code.toLowerCase()
      break
    case 'famiglia_label':
      av = (a.famiglia_label ?? '').toLowerCase()
      bv = (b.famiglia_label ?? '').toLowerCase()
      break
    case 'requested_date': {
      const ad = resolveRequestedDate(a)
      const bd = resolveRequestedDate(b)
      const at = ad ? new Date(`${ad}T00:00:00`).getTime() : Number.POSITIVE_INFINITY
      const bt = bd ? new Date(`${bd}T00:00:00`).getTime() : Number.POSITIVE_INFINITY
      av = Number.isNaN(at) ? Number.POSITIVE_INFINITY : at
      bv = Number.isNaN(bt) ? Number.POSITIVE_INFINITY : bt
      break
    }
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

// ─── Badge family / motivi ───────────────────────────────────────────────────

const FAMILY_BADGE_CLASSES = [
  'bg-sky-50 text-sky-700 border border-sky-200',
  'bg-emerald-50 text-emerald-700 border border-emerald-200',
  'bg-amber-50 text-amber-700 border border-amber-200',
  'bg-rose-50 text-rose-700 border border-rose-200',
  'bg-indigo-50 text-indigo-700 border border-indigo-200',
  'bg-cyan-50 text-cyan-700 border border-cyan-200',
]

function familyBadgeClass(label: string | null): string {
  if (!label) return 'bg-muted text-muted-foreground border border-border'
  const key = label.trim().toUpperCase()
  let hash = 0
  for (let i = 0; i < key.length; i += 1) hash = (hash * 31 + key.charCodeAt(i)) >>> 0
  return FAMILY_BADGE_CLASSES[hash % FAMILY_BADGE_CLASSES.length]
}

function FamilyBadge({ label }: { label: string | null }) {
  if (!label) return <span className="text-muted-foreground/50 italic">—</span>
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${familyBadgeClass(label)}`}>
      {label}
    </span>
  )
}

function DriverBadges({ item }: { item: PlanningCandidateItem }) {
  const hasCustomer = (parseFloat(item.customer_shortage_qty ?? '0') || 0) > 0
  const hasStock = (parseFloat(item.stock_replenishment_qty ?? '0') || 0) > 0

  if (!hasCustomer && !hasStock) {
    if (item.primary_driver === 'customer') {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">Cliente</span>
    }
    if (item.primary_driver === 'stock') {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-50 text-orange-700 border border-orange-200">Scorta</span>
    }
    return <span className="text-muted-foreground/50 italic">—</span>
  }

  return (
    <div className="flex items-center gap-1">
      {hasCustomer && (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">Cliente</span>
      )}
      {hasStock && (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-50 text-orange-700 border border-orange-200">Scorta</span>
      )}
    </div>
  )
}

function boolFromTriState(v: TriState): boolean | null {
  if (v === 'true') return true
  if (v === 'false') return false
  return null
}

function triStateFromBool(v: boolean | null | undefined): TriState {
  if (v === true) return 'true'
  if (v === false) return 'false'
  return 'null'
}

function parseOptionalNumber(v: string): number | null {
  const n = parseFloat(v.replace(',', '.'))
  return isNaN(n) ? null : n
}

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}

function QuickConfigModal({
  articleCode,
  famiglie,
  detail,
  loading,
  saving,
  onClose,
  onSave,
}: {
  articleCode: string
  famiglie: FamigliaItem[]
  detail: ArticoloDetail | null
  loading: boolean
  saving: boolean
  onClose: () => void
  onSave: (payload: {
    famigliaCode: string | null
    gestioneScorteOverride: boolean | null
    stockMonthsOverride: number | null
    stockTriggerMonthsOverride: number | null
    capacityOverrideQty: number | null
  }) => Promise<void>
}) {
  const [famigliaCode, setFamigliaCode] = useState<string>('')
  const [gestioneScorte, setGestioneScorte] = useState<TriState>('null')
  const [stockMonthsInput, setStockMonthsInput] = useState('')
  const [stockTriggerInput, setStockTriggerInput] = useState('')
  const [capacityOverrideInput, setCapacityOverrideInput] = useState('')

  useEffect(() => {
    if (!detail) return
    setFamigliaCode(detail.famiglia_code ?? '')
    setGestioneScorte(triStateFromBool(detail.override_gestione_scorte_attiva))
    setStockMonthsInput(detail.override_stock_months ?? '')
    setStockTriggerInput(detail.override_stock_trigger_months ?? '')
    setCapacityOverrideInput(detail.capacity_override_qty ?? '')
  }, [detail?.codice_articolo]) // eslint-disable-line react-hooks/exhaustive-deps

  const saveDisabled = loading || saving || detail == null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-background border rounded-xl shadow-lg w-full max-w-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-base">Quick Config Articolo</h2>
            <p className="text-xs text-muted-foreground font-mono">{articleCode}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none">
            ×
          </button>
        </div>

        {loading && (
          <div className="text-sm text-muted-foreground">Caricamento dettaglio articolo…</div>
        )}

        {!loading && detail && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-xs text-muted-foreground">Famiglia</span>
              <select
                value={famigliaCode}
                onChange={(e) => setFamigliaCode(e.target.value)}
                className="w-full border rounded-md px-2 py-1.5 text-sm"
                disabled={saving}
              >
                <option value="">(nessuna)</option>
                {famiglie.map((f) => (
                  <option key={f.code} value={f.code}>{f.label}</option>
                ))}
              </select>
            </label>

            <label className="space-y-1">
              <span className="text-xs text-muted-foreground">Gestione scorte (override)</span>
              <select
                value={gestioneScorte}
                onChange={(e) => setGestioneScorte(e.target.value as TriState)}
                className="w-full border rounded-md px-2 py-1.5 text-sm"
                disabled={saving}
              >
                <option value="null">Eredita famiglia</option>
                <option value="true">Attiva</option>
                <option value="false">Disattiva</option>
              </select>
            </label>

            <label className="space-y-1">
              <span className="text-xs text-muted-foreground">Stock months (override)</span>
              <input
                type="text"
                value={stockMonthsInput}
                onChange={(e) => setStockMonthsInput(e.target.value)}
                placeholder={detail.effective_stock_months ?? 'eredita famiglia'}
                className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                disabled={saving}
              />
            </label>

            <label className="space-y-1">
              <span className="text-xs text-muted-foreground">Stock trigger months (override)</span>
              <input
                type="text"
                value={stockTriggerInput}
                onChange={(e) => setStockTriggerInput(e.target.value)}
                placeholder={detail.effective_stock_trigger_months ?? 'eredita famiglia'}
                className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                disabled={saving}
              />
            </label>

            <label className="space-y-1 md:col-span-2">
              <span className="text-xs text-muted-foreground">Capacity override qty</span>
              <input
                type="text"
                value={capacityOverrideInput}
                onChange={(e) => setCapacityOverrideInput(e.target.value)}
                placeholder="vuoto = nessun override"
                className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                disabled={saving}
              />
            </label>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="py-1.5 px-3 border rounded-md text-sm hover:bg-muted transition-colors"
            disabled={saving}
          >
            Annulla
          </button>
          <button
            type="button"
            disabled={saveDisabled}
            onClick={() =>
              onSave({
                famigliaCode: famigliaCode || null,
                gestioneScorteOverride: boolFromTriState(gestioneScorte),
                stockMonthsOverride: parseOptionalNumber(stockMonthsInput),
                stockTriggerMonthsOverride: parseOptionalNumber(stockTriggerInput),
                capacityOverrideQty: parseOptionalNumber(capacityOverrideInput),
              })
            }
            className="py-1.5 px-3 rounded-md text-sm font-medium bg-foreground text-background disabled:opacity-50"
          >
            {saving ? 'Salvataggio…' : 'Salva'}
          </button>
        </div>
      </div>
    </div>
  )
}

function warningBadgeClass(code: string): string {
  if (code === 'INVALID_STOCK_CAPACITY') {
    return 'bg-red-50 text-red-700 border border-red-200'
  }
  return 'bg-amber-50 text-amber-700 border border-amber-200'
}

function warningBadgeLabel(code: string): string {
  if (code === 'INVALID_STOCK_CAPACITY') return 'Capacity'
  return code
}

function WarningBadges({ item }: { item: PlanningCandidateItem }) {
  if (item.active_warnings.length === 0) {
    return <span className="text-muted-foreground/50 italic">—</span>
  }

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {item.active_warnings.map((warning, idx) => (
        <span
          key={`${item.article_code}-warn-${warning.code}-${idx}`}
          title={warning.message}
          className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${warningBadgeClass(warning.code)}`}
        >
          {warningBadgeLabel(warning.code)}
        </span>
      ))}
    </div>
  )
}

// ─── Header ───────────────────────────────────────────────────────────────────

function PageHeader({
  totalCount,
  shownCount,
  selectedCount,
  loadStatus,
  syncStatus,
  onRefresh,
  onGenerateProposals,
  generateBusy,
}: {
  totalCount: number
  shownCount: number
  selectedCount: number
  loadStatus: LoadStatus
  syncStatus: SyncStatus
  onRefresh: () => void
  onGenerateProposals: () => void
  generateBusy: boolean
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
        <div className="flex items-center gap-2">
          {selectedCount > 0 && (
            <span className="text-xs text-muted-foreground">
              {selectedCount} selezionat{selectedCount === 1 ? 'o' : 'i'}
            </span>
          )}
          <button
            onClick={onGenerateProposals}
            disabled={busy || generateBusy || selectedCount === 0}
            className="py-1 px-3 border rounded-md text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
          >
            {generateBusy ? 'Generazione…' : 'Genera proposte'}
          </button>
          <button
            onClick={onRefresh}
            disabled={busy || generateBusy}
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
  selectedSourceIds,
  sortKey,
  sortDir,
  onSort,
  onOpenQuickConfig,
  onToggleSelected,
  onToggleSelectAll,
}: {
  items: PlanningCandidateItem[]
  selectedSourceIds: string[]
  sortKey: SortKey
  sortDir: SortDir
  onSort: (k: SortKey) => void
  onOpenQuickConfig: (articleCode: string) => void
  onToggleSelected: (sourceCandidateId: string) => void
  onToggleSelectAll: (selectAll: boolean) => void
}) {
  const allSelected = items.length > 0 && items.every((item) => selectedSourceIds.includes(item.source_candidate_id))

  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-background">
          <tr>
            <th className={thBase}>
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onToggleSelectAll(e.target.checked)}
              />
            </th>
            <Th
              label="Codice"
              sortKey="article_code"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
            />
            <th className={thBase}>Descrizione</th>
            <th className={thBase}>Misura</th>
            <Th
              label="Famiglia"
              sortKey="famiglia_label"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
            />
            <th className={thBase}>Motivi</th>
            <th className={thBase}>Warnings</th>
            <th className={thBase}>Destinazione</th>
            <Th
              label="Data richiesta"
              sortKey="requested_date"
              currentKey={sortKey}
              dir={sortDir}
              onSort={onSort}
            />
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
            const rowKey = item.source_candidate_id

            // Valori unificati per le colonne condivise
            const demandVal = isByCol ? item.line_open_demand_qty : item.customer_open_demand_qty
            const supplyVal = isByCol ? item.linked_incoming_supply_qty : item.incoming_supply_qty
            const coverageVal = isByCol ? item.line_future_coverage_qty : item.future_availability_qty
            const requestedDate = resolveRequestedDate(item)
            const descLines = resolveDescriptionLines(item)

            return (
              <tr
                key={rowKey}
                className="border-b last:border-b-0 hover:bg-muted/30 transition-colors"
              >
                <td className={tdCls}>
                  <input
                    type="checkbox"
                    checked={selectedSourceIds.includes(item.source_candidate_id)}
                    onChange={() => onToggleSelected(item.source_candidate_id)}
                  />
                </td>
                <td className={tdCls}>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs">{item.article_code}</span>
                    <button
                      type="button"
                      onClick={() => onOpenQuickConfig(item.article_code)}
                      className="text-[11px] px-1.5 py-0.5 border rounded hover:bg-muted transition-colors"
                      title="Quick config articolo"
                    >
                      ⚙
                    </button>
                  </div>
                </td>
                <td className={tdCls}>
                  <div className="flex flex-col gap-0.5">
                    {descLines.map((line, idx) => (
                      <span key={`${rowKey}-desc-${idx}`} className="text-foreground">
                        {line}
                      </span>
                    ))}
                  </div>
                </td>
                <td className={tdCls}>
                  {item.misura ? (
                    <span className="font-mono text-xs text-muted-foreground">{item.misura}</span>
                  ) : (
                    <span className="text-muted-foreground/50 italic">—</span>
                  )}
                </td>
                <td className={tdCls}>
                  <FamilyBadge label={item.famiglia_label} />
                </td>
                <td className={tdCls}>
                  <DriverBadges item={item} />
                </td>
                <td className={tdCls}>
                  <WarningBadges item={item} />
                </td>
                <td className={tdCls}>
                  {item.requested_destination_display ? (
                    <span className="text-muted-foreground">{item.requested_destination_display}</span>
                  ) : item.primary_driver === 'stock' ? (
                    <span className="text-muted-foreground/60 italic text-xs">solo scorta</span>
                  ) : (
                    <span className="text-muted-foreground/50 italic">—</span>
                  )}
                </td>
                <td className={tdCls}>
                  {requestedDate ? (
                    <span className="font-mono text-xs text-muted-foreground">{fmtDate(requestedDate)}</span>
                  ) : item.primary_driver === 'stock' ? (
                    <span className="text-muted-foreground/60 italic text-xs">solo scorta</span>
                  ) : (
                    <span className="text-muted-foreground/50 italic">—</span>
                  )}
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
  const navigate = useNavigate()
  const [items, setItems] = useState<PlanningCandidateItem[]>([])
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [generateBusy, setGenerateBusy] = useState(false)
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])

  // Filtri
  const [soloInProduzione, setSoloInProduzione] = useState(true)
  const [filterCodice, setFilterCodice] = useState('')
  const [filterDesc, setFilterDesc] = useState('')
  const [famigliaFilter, setFamigliaFilter] = useState('')
  // Filtri driver + horizon (TASK-V2-102)
  const [driverFilter, setDriverFilter] = useState<DriverFilter>('tutti')
  const [soloEntroHorizon, setSoloEntroHorizon] = useState(false)
  const [horizonDays, setHorizonDays] = useState(30)
  const [famiglieConfig, setFamiglieConfig] = useState<FamigliaItem[]>([])
  const [quickConfigArticleCode, setQuickConfigArticleCode] = useState<string | null>(null)
  const [quickConfigDetail, setQuickConfigDetail] = useState<ArticoloDetail | null>(null)
  const [quickConfigLoading, setQuickConfigLoading] = useState(false)
  const [quickConfigSaving, setQuickConfigSaving] = useState(false)

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

  useEffect(() => {
    apiClient
      .get<FamigliaItem[]>('/produzione/famiglie')
      .then((r) => setFamiglieConfig(r.data))
      .catch(() => {})
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
        if (i.planning_mode === 'by_customer_order_line') {
          return isDateWithinHorizon(i.requested_delivery_date, horizonDays)
        }
        return i.is_within_customer_horizon === true
      })
  }, [items, soloInProduzione, filterCodice, filterDesc, famigliaFilter, driverFilter, soloEntroHorizon, horizonDays])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => cmpItems(a, b, sortKey, sortDir))
  }, [filtered, sortKey, sortDir])

  useEffect(() => {
    const visibleIds = new Set(items.map((item) => item.source_candidate_id))
    setSelectedSourceIds((prev) => prev.filter((id) => visibleIds.has(id)))
  }, [items])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'required_qty_minimum' ? 'desc' : 'asc')
    }
  }

  const openQuickConfig = async (articleCode: string) => {
    setQuickConfigArticleCode(articleCode)
    setQuickConfigLoading(true)
    setQuickConfigDetail(null)
    try {
      const { data } = await apiClient.get<ArticoloDetail>(
        `/produzione/articoli/${encodeURIComponent(articleCode)}`,
      )
      setQuickConfigDetail(data)
    } catch {
      toast.error('Impossibile caricare il dettaglio articolo')
      setQuickConfigArticleCode(null)
    } finally {
      setQuickConfigLoading(false)
    }
  }

  const closeQuickConfig = () => {
    setQuickConfigArticleCode(null)
    setQuickConfigDetail(null)
    setQuickConfigLoading(false)
    setQuickConfigSaving(false)
  }

  const saveQuickConfig = async (payload: {
    famigliaCode: string | null
    gestioneScorteOverride: boolean | null
    stockMonthsOverride: number | null
    stockTriggerMonthsOverride: number | null
    capacityOverrideQty: number | null
  }) => {
    if (!quickConfigArticleCode) return
    setQuickConfigSaving(true)
    try {
      await apiClient.patch(
        `/produzione/articoli/${encodeURIComponent(quickConfigArticleCode)}/famiglia`,
        { famiglia_code: payload.famigliaCode },
      )
      await apiClient.patch<ArticoloDetail>(
        `/produzione/articoli/${encodeURIComponent(quickConfigArticleCode)}/gestione-scorte-override`,
        { override_gestione_scorte_attiva: payload.gestioneScorteOverride },
      )
      await apiClient.patch<ArticoloDetail>(
        `/produzione/articoli/${encodeURIComponent(quickConfigArticleCode)}/stock-policy-override`,
        {
          override_stock_months: payload.stockMonthsOverride,
          override_stock_trigger_months: payload.stockTriggerMonthsOverride,
          capacity_override_qty: payload.capacityOverrideQty,
        },
      )
      const { data } = await apiClient.get<ArticoloDetail>(
        `/produzione/articoli/${encodeURIComponent(quickConfigArticleCode)}`,
      )
      setQuickConfigDetail(data)
      await loadCandidates()
      toast.success('Configurazione articolo aggiornata')
      closeQuickConfig()
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore durante il salvataggio configurazione'))
    } finally {
      setQuickConfigSaving(false)
    }
  }

  const handleGenerateProposals = async () => {
    if (selectedSourceIds.length === 0) return
    setGenerateBusy(true)
    try {
      const { data } = await apiClient.post<ProposalWorkspaceGenerateResult>(
        '/produzione/planning-candidates/generate-proposals-workspace',
        { source_candidate_ids: selectedSourceIds },
        { params: { horizon_days: horizonDaysRef.current } },
      )
      toast.success(
        `Workspace creato: ${data.created_count} righe${data.skipped_missing_count > 0 ? `, ${data.skipped_missing_count} saltate` : ''}`,
      )
      setSelectedSourceIds([])
      navigate(`/produzione/proposals?workspace_id=${encodeURIComponent(data.workspace_id)}`)
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore durante la generazione workspace proposal'))
    } finally {
      setGenerateBusy(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        totalCount={filtered.length}
        shownCount={sorted.length}
        selectedCount={selectedSourceIds.length}
        loadStatus={loadStatus}
        syncStatus={syncStatus}
        onRefresh={handleRefresh}
        onGenerateProposals={handleGenerateProposals}
        generateBusy={generateBusy}
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
          selectedSourceIds={selectedSourceIds}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={handleSort}
          onOpenQuickConfig={openQuickConfig}
          onToggleSelected={(sourceCandidateId) => {
            setSelectedSourceIds((prev) => (
              prev.includes(sourceCandidateId)
                ? prev.filter((id) => id !== sourceCandidateId)
                : [...prev, sourceCandidateId]
            ))
          }}
          onToggleSelectAll={(selectAll) => {
            setSelectedSourceIds((prev) => {
              const visibleIds = sorted.map((item) => item.source_candidate_id)
              if (selectAll) {
                return Array.from(new Set([...prev, ...visibleIds]))
              }
              return prev.filter((id) => !visibleIds.includes(id))
            })
          }}
        />
      )}

      {quickConfigArticleCode && (
        <QuickConfigModal
          articleCode={quickConfigArticleCode}
          famiglie={famiglieConfig}
          detail={quickConfigDetail}
          loading={quickConfigLoading}
          saving={quickConfigSaving}
          onClose={closeQuickConfig}
          onSave={saveQuickConfig}
        />
      )}
    </div>
  )
}
