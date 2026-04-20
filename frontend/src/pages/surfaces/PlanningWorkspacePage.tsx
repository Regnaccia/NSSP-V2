/**
 * Surface Produzione — Planning Workspace (shadow view, TASK-V2-137, TASK-V2-138, TASK-V2-139, TASK-V2-140, TASK-V2-152).
 *
 * Vista parallela alla tabella `PlanningCandidatesPage` per validare
 * il target architetturale Unified Planning Workspace a 3 colonne.
 *
 * Scope:
 *   - colonna sinistra: inbox sintetica dei candidate (UIX_SPEC_PLANNING_CANDIDATES §Left Column)
 *   - colonna centrale: dettaglio candidate (UIX_SPEC_PLANNING_CANDIDATES §Center Column)
 *   - colonna destra: Proposta (TASK-V2-152) | Planning/Scorte editabile (TASK-V2-140)
 *
 * La vista corrente `/produzione/planning-candidates` resta invariata e disponibile per confronto.
 * Consuma lo stesso endpoint GET /produzione/planning-candidates (read model Core invariato).
 *
 * Gerarchia card sinistra (TASK-V2-138):
 *   1. cliente_scope_label (+ triangolo warning top-right)
 *   2. article_code – misura
 *   3. display_description
 *   4. destinazione + data (solo se customer)
 *   5. badge: proposal_status / workflow_status / release_status
 *   qty sintetica: required_qty_eventual (right-aligned)
 *
 * Ordine blocchi centrali (TASK-V2-138 + TASK-V2-140):
 *   Identità → Cliente/Ordine → Need vs Release → Stock/Capienza →
 *   Parametri di calcolo (by_article only) → Motivo → Warnings → Priority
 *
 * proposal_status e workflow_status non sono ancora contratti backend:
 *   - proposal_status: derivato da release_status per by_article
 *   - workflow_status: sempre "Inattivo" (placeholder)
 */

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import { proposalLogicMeta } from '@/lib/proposalLogicMeta'
import type { ArticoloDetail, PlanningCandidateItem, SyncSurfaceResponse } from '@/types/api'

// ─── Tipi locali ──────────────────────────────────────────────────────────────

type LoadStatus = 'loading' | 'idle' | 'error'
type SyncStatus = 'idle' | 'syncing'

// proposal_status e workflow_status: derivati / placeholder (nessun contratto backend ancora)
type ProposalStatus = 'valid_for_export' | 'need_review' | 'error'
type WorkflowStatus = 'inattivo' | 'preso_in_carico' | 'in_batch_export'

/** Filtro scope sinistra (TASK-V2-139) */
type ScopeFilter = 'tutti' | 'solo_clienti' | 'solo_magazzino'
/** Sorting colonna sinistra (TASK-V2-139) */
type SortBy = 'codice' | 'data_consegna' | 'priority_score'
/** Pannello colonna destra (TASK-V2-140, TASK-V2-152) */
type RightPanel = 'none' | 'planning_scorte' | 'proposal'

// ─── Utility ──────────────────────────────────────────────────────────────────

function fmtQty(val: string | null | undefined): string {
  if (val == null) return '—'
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 3 })
}

function fmtDate(val: string | null | undefined): string {
  if (!val) return '—'
  const d = new Date(`${val}T00:00:00`)
  if (isNaN(d.getTime())) return val
  return d.toLocaleDateString('it-IT')
}

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

/** Ricerca cliente su requested_destination_display (TASK-V2-139) */
function matchesCliente(item: PlanningCandidateItem, raw: string): boolean {
  if (!raw.trim()) return true
  return (item.requested_destination_display ?? '').toLowerCase().includes(raw.trim().toLowerCase())
}

function resolveRequestedDate(item: PlanningCandidateItem): string | null {
  return item.planning_mode === 'by_customer_order_line'
    ? item.requested_delivery_date
    : item.earliest_customer_delivery_date
}

/**
 * Quantità sintetica per la card sinistra (TASK-V2-138):
 * required_qty_eventual per by_article con capacity configurata,
 * fallback su required_qty_minimum per gli altri casi.
 */
function resolveQtySintetica(item: PlanningCandidateItem): string {
  return item.required_qty_eventual ?? item.required_qty_minimum
}

// ─── Derivazioni semantiche per la shadow view ────────────────────────────────

/**
 * cliente_scope_label: derivato da primary_driver e componenti shortage/replenishment.
 * Per by_customer_order_line: sempre "Cliente".
 */
function clienteScopeLabel(item: PlanningCandidateItem): string {
  if (item.planning_mode === 'by_customer_order_line') return 'Cliente'
  const hasCustomer =
    parseFloat(item.customer_shortage_qty ?? '0') > 0 || item.primary_driver === 'customer'
  const hasStock =
    parseFloat(item.stock_replenishment_qty ?? '0') > 0 || item.primary_driver === 'stock'
  if (hasCustomer && hasStock) return 'Cliente + Magazzino'
  if (hasCustomer) return 'Cliente'
  return 'Magazzino'
}

/**
 * proposal_status: derivato da release_status per by_article.
 * Per by_customer_order_line: "need_review" come placeholder (nessun contratto release yet).
 */
function deriveProposalStatus(item: PlanningCandidateItem): ProposalStatus {
  if (item.planning_mode === 'by_customer_order_line') return 'need_review'
  switch (item.release_status) {
    case 'launchable_now':
      return 'valid_for_export'
    case 'launchable_partially':
      return 'need_review'
    case 'blocked_by_capacity_now':
      return 'error'
    default:
      return 'need_review'
  }
}

/**
 * workflow_status: sempre "inattivo" — workspace state non ancora persistito nel backend.
 */
function deriveWorkflowStatus(_item: PlanningCandidateItem): WorkflowStatus {
  return 'inattivo'
}

// ─── Provenance helpers (TASK-V2-140) ─────────────────────────────────────────

/**
 * Provenienza per parametri stock con override articolo / default famiglia.
 * Vocabolario: "default famiglia" | "override articolo" | "—"
 */
function provenanceStockParam(overrideVal: unknown, famigliaCode: string | null): string {
  if (overrideVal !== null && overrideVal !== undefined) return 'override articolo'
  if (famigliaCode) return 'default famiglia'
  return '—'
}

/**
 * Provenienza per la capacity effettiva.
 * Vocabolario: "override articolo" | "calcolato"
 */
function provenanceCapacity(capacityOverrideQty: string | null): string {
  return capacityOverrideQty !== null ? 'override articolo' : 'calcolato'
}

function ProvenancePill({ label }: { label: string }) {
  if (label === '—') return <span className="text-muted-foreground/40 italic text-[10px]">—</span>
  return (
    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground border shrink-0">
      {label}
    </span>
  )
}

// ─── Badge components ─────────────────────────────────────────────────────────

const PROPOSAL_STATUS_CFG: Record<ProposalStatus, { label: string; cls: string }> = {
  valid_for_export: { label: 'Export OK',     cls: 'bg-green-50 text-green-700 border border-green-200' },
  need_review:      { label: 'Da verificare', cls: 'bg-amber-50 text-amber-700 border border-amber-200' },
  error:            { label: 'Errore',        cls: 'bg-red-50 text-red-700 border border-red-200' },
}

function ProposalStatusBadge({ status }: { status: ProposalStatus }) {
  const cfg = PROPOSAL_STATUS_CFG[status]
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold whitespace-nowrap ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

const WORKFLOW_STATUS_CFG: Record<WorkflowStatus, { label: string; cls: string }> = {
  inattivo:         { label: 'Inattivo',      cls: 'bg-muted text-muted-foreground border border-border' },
  preso_in_carico:  { label: 'In carico',     cls: 'bg-blue-50 text-blue-700 border border-blue-200' },
  in_batch_export:  { label: 'In batch',      cls: 'bg-indigo-50 text-indigo-700 border border-indigo-200' },
}

function WorkflowStatusBadge({ status }: { status: WorkflowStatus }) {
  const cfg = WORKFLOW_STATUS_CFG[status]
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

const RELEASE_STATUS_CFG: Record<string, { label: string; cls: string }> = {
  launchable_now:          { label: 'Lanciabile', cls: 'bg-green-50 text-green-700 border border-green-200' },
  launchable_partially:    { label: 'Parziale',   cls: 'bg-amber-50 text-amber-700 border border-amber-200' },
  blocked_by_capacity_now: { label: 'Bloccato',   cls: 'bg-red-50 text-red-700 border border-red-200' },
}

function ReleaseStatusBadge({ status }: { status: string | null }) {
  if (!status) return null
  const cfg = RELEASE_STATUS_CFG[status]
  if (!cfg) return null
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

function ScopeBadge({ label }: { label: string }) {
  const cls =
    label === 'Cliente'
      ? 'bg-blue-50 text-blue-700 border border-blue-200'
      : label === 'Magazzino'
      ? 'bg-orange-50 text-orange-700 border border-orange-200'
      : 'bg-purple-50 text-purple-700 border border-purple-200'
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cls}`}>
      {label}
    </span>
  )
}

function PriorityBandBadge({ band, score }: { band: string; score: number | null }) {
  const cls =
    band === 'critical'
      ? 'bg-red-50 text-red-700 border border-red-200'
      : band === 'high'
      ? 'bg-orange-50 text-orange-700 border border-orange-200'
      : band === 'medium'
      ? 'bg-yellow-50 text-yellow-700 border border-yellow-200'
      : 'bg-gray-50 text-gray-500 border border-gray-200'
  const label =
    band === 'critical' ? 'critico' : band === 'high' ? 'alto' : band === 'medium' ? 'medio' : 'basso'
  const title = score != null ? `Priority score: ${score}` : `Priorità: ${label}`
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap ${cls}`} title={title}>
      {label}
    </span>
  )
}

// ─── Left Column ──────────────────────────────────────────────────────────────

function CandidateCard({
  item,
  selected,
  onClick,
}: {
  item: PlanningCandidateItem
  selected: boolean
  onClick: () => void
}) {
  const proposalStatus = deriveProposalStatus(item)
  const workflowStatus = deriveWorkflowStatus(item)
  const scopeLabel = clienteScopeLabel(item)
  const requestedDate = resolveRequestedDate(item)
  const hasCustomer = item.primary_driver === 'customer' || item.planning_mode === 'by_customer_order_line'
  const hasWarnings = item.active_warnings.length > 0
  const qtySintetica = resolveQtySintetica(item)

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left px-3 py-2.5 border-b flex flex-col gap-1.5 transition-colors ${
        selected
          ? 'bg-foreground/5 border-l-2 border-l-foreground'
          : 'hover:bg-muted/40 border-l-2 border-l-transparent'
      }`}
    >
      {/* Riga 1: scope label + triangolo warning (top-right) */}
      <div className="flex items-center justify-between gap-1.5">
        <ScopeBadge label={scopeLabel} />
        {hasWarnings && (
          <span
            className="text-red-500 text-[11px] leading-none"
            title={item.active_warnings.map((w) => w.message).join(' | ')}
          >
            ▲
          </span>
        )}
      </div>

      {/* Riga 2: article_code – misura + qty sintetica right */}
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono text-xs font-semibold text-foreground">
          {item.article_code}
          {item.misura && (
            <span className="font-normal text-muted-foreground"> – {item.misura}</span>
          )}
        </span>
        <span className="font-mono tabular-nums text-xs text-foreground/70 shrink-0">
          {fmtQty(qtySintetica)}
        </span>
      </div>

      {/* Riga 3: descrizione */}
      <span className="text-xs text-muted-foreground truncate leading-snug">
        {item.display_description || item.display_label}
      </span>

      {/* Riga 4: destinazione + data (solo se customer) */}
      {hasCustomer && (item.requested_destination_display || requestedDate) && (
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          {item.requested_destination_display && (
            <span className="truncate">{item.requested_destination_display}</span>
          )}
          {item.requested_destination_display && requestedDate && (
            <span>·</span>
          )}
          {requestedDate && (
            <span className="shrink-0">{fmtDate(requestedDate)}</span>
          )}
        </div>
      )}

      {/* Riga 5: badge stati + priority_band */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <ProposalStatusBadge status={proposalStatus} />
        <WorkflowStatusBadge status={workflowStatus} />
        {item.release_status && (
          <ReleaseStatusBadge status={item.release_status} />
        )}
        {item.priority_band && (
          <PriorityBandBadge band={item.priority_band} score={item.priority_score} />
        )}
      </div>
    </button>
  )
}

function LeftColumn({
  items,
  selectedId,
  onSelect,
}: {
  items: PlanningCandidateItem[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center flex-1 p-8 text-xs text-muted-foreground">
        Nessun candidate nel perimetro corrente.
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {items.map((item) => (
        <CandidateCard
          key={item.source_candidate_id}
          item={item}
          selected={item.source_candidate_id === selectedId}
          onClick={() => onSelect(item.source_candidate_id)}
        />
      ))}
    </div>
  )
}

// ─── Center Column — blocchi dettaglio ────────────────────────────────────────

function BlockHeader({ title }: { title: string }) {
  return (
    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
      {title}
    </h3>
  )
}

/**
 * Riga di griglia 2-col compatta: label | value.
 * Renderizza un Fragment — deve essere figlio diretto di un contenitore CSS grid
 * con gridTemplateColumns: 'max-content auto' (stessa convenzione TASK-V2-141).
 */
function FieldRow({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <>
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={mono ? 'font-mono tabular-nums text-xs' : 'text-sm'}>{value}</span>
    </>
  )
}


// 1. Identità — article_code, misura, descrizione, warning triangle (TASK-V2-138: no cliente_scope_label)
function BloccoIdentita({ item }: { item: PlanningCandidateItem }) {
  const hasWarnings = item.active_warnings.length > 0
  return (
    <div className="border rounded-lg p-3 space-y-1.5">
      <BlockHeader title="Identità" />
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-0.5">
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-sm font-semibold">{item.article_code}</span>
            {item.misura && (
              <span className="font-mono text-xs text-muted-foreground">– {item.misura}</span>
            )}
          </div>
          {item.famiglia_label && (
            <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground border">
              {item.famiglia_label}
            </span>
          )}
        </div>
        {hasWarnings && (
          <span className="text-red-500 text-xs shrink-0 mt-0.5">▲</span>
        )}
      </div>
      <p className="text-sm text-foreground">{item.display_description || item.display_label}</p>
    </div>
  )
}

// 3. Need vs Release
function BloccoNeedVsRelease({ item }: { item: PlanningCandidateItem }) {
  const isByCol = item.planning_mode === 'by_customer_order_line'
  return (
    <div className="border rounded-lg p-3">
      <BlockHeader title="Need vs Release" />
      <div
        className="items-baseline gap-y-1.5"
        style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}
      >
        {!isByCol ? (
          <>
            <FieldRow label="Shortage cliente" value={fmtQty(item.customer_shortage_qty)} mono />
            <FieldRow label="Replenishment scorta" value={fmtQty(item.stock_replenishment_qty)} mono />
            <FieldRow label="Fabbisogno totale" value={<span className="font-semibold">{fmtQty(item.required_qty_eventual)}</span>} />
            <FieldRow
              label="Rilascio ora (max)"
              value={
                item.release_qty_now_max != null ? (
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono tabular-nums text-xs">{fmtQty(item.release_qty_now_max)}</span>
                    {item.release_status && <ReleaseStatusBadge status={item.release_status} />}
                  </div>
                ) : (
                  <span className="text-muted-foreground/50 italic text-xs">—</span>
                )
              }
            />
          </>
        ) : (
          <>
            <FieldRow label="Domanda riga aperta" value={fmtQty(item.line_open_demand_qty)} mono />
            <FieldRow label="Supply collegata" value={fmtQty(item.linked_incoming_supply_qty)} mono />
            <FieldRow
              label="Copertura futura"
              value={
                <span className={parseFloat(item.line_future_coverage_qty ?? '0') < 0 ? 'text-red-600 font-semibold' : ''}>
                  {fmtQty(item.line_future_coverage_qty)}
                </span>
              }
            />
            <FieldRow label="Fabbisogno minimo" value={<span className="font-semibold">{fmtQty(item.required_qty_minimum)}</span>} />
          </>
        )}
      </div>
    </div>
  )
}

// 5. Motivo
function BloccoMotivo({ item }: { item: PlanningCandidateItem }) {
  return (
    <div className="border rounded-lg p-3 space-y-2">
      <BlockHeader title="Motivo" />
      <div className="flex items-center gap-2">
        {item.primary_driver === 'customer' && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">Cliente</span>
        )}
        {item.primary_driver === 'stock' && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-50 text-orange-700 border border-orange-200">Scorta</span>
        )}
        <span className="text-xs font-mono text-muted-foreground">{item.reason_code}</span>
      </div>
      <p className="text-sm text-foreground">{item.reason_text}</p>
    </div>
  )
}

// 2. Cliente / Ordine (TASK-V2-138 + TASK-V2-143):
//    - include cliente_scope_label
//    - nascosto nei casi stock-only (primary_driver === 'stock' e by_article)
//    - per by_customer_order_line: no duplicazione della descrizione ordine (già in display_description)
//    - sottosezione Ordini aperti solo per by_article (TASK-V2-143)
function BloccoClienteOrdine({ item, horizonDays }: { item: PlanningCandidateItem; horizonDays: number }) {
  const isByCol = item.planning_mode === 'by_customer_order_line'

  const scopeLabel = clienteScopeLabel(item)
  const requestedDate = resolveRequestedDate(item)

  return (
    <div className="border rounded-lg p-3 space-y-3">
      <BlockHeader title="Cliente / Ordine" />
      <div
        className="items-baseline gap-y-1.5"
        style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}
      >
        <FieldRow label="Scope" value={<ScopeBadge label={scopeLabel} />} />
        {item.requested_destination_display && (
          <FieldRow label="Destinazione" value={item.requested_destination_display} />
        )}
        {requestedDate && (
          <FieldRow label="Data richiesta" value={fmtDate(requestedDate)} mono />
        )}
        {item.order_reference && (
          <FieldRow
            label="Ordine / Riga"
            value={
              <span className="font-mono text-xs">
                {item.order_reference}
                {item.line_reference != null && (
                  <span className="text-muted-foreground"> / {item.line_reference}</span>
                )}
              </span>
            }
          />
        )}
        {/* full_order_line_description omessa per by_customer_order_line:
            già espressa in display_description nel blocco Identità */}
        {!isByCol && item.full_order_line_description && (
          <FieldRow label="Descrizione riga" value={item.full_order_line_description} />
        )}
      </div>

      {/* Ordini aperti — solo by_article (TASK-V2-143) */}
      {!isByCol && item.open_order_lines.length > 0 && (
        <BloccoOrdiniAperti lines={item.open_order_lines} horizonDays={horizonDays} />
      )}
    </div>
  )
}

/** Sottosezione Ordini aperti (TASK-V2-143) — usata dentro BloccoClienteOrdine */
function BloccoOrdiniAperti({
  lines,
  horizonDays,
}: {
  lines: PlanningCandidateItem['open_order_lines']
  horizonDays: number
}) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const horizonDate = new Date(today)
  horizonDate.setDate(today.getDate() + horizonDays)

  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">
        Ordini aperti
      </p>
      <div className="space-y-1">
        {lines.map((line) => {
          const d = line.requested_delivery_date
            ? new Date(`${line.requested_delivery_date}T00:00:00`)
            : null
          const withinHorizon = d != null ? d <= horizonDate : null

          const rowCls =
            withinHorizon === true
              ? 'bg-blue-50 border-blue-200 text-blue-900'
              : withinHorizon === false
              ? 'bg-amber-50 border-amber-200 text-amber-900'
              : 'bg-muted/40 border-border text-foreground'

          return (
            <div
              key={`${line.order_reference}-${line.line_reference}`}
              className={`flex items-center justify-between gap-2 px-2 py-1 rounded border text-xs ${rowCls}`}
            >
              <div className="flex items-center gap-2 min-w-0">
                {/* Data consegna */}
                <span className="font-mono tabular-nums shrink-0 text-[11px]">
                  {d ? fmtDate(line.requested_delivery_date) : '—'}
                </span>
                {/* Riferimento ordine */}
                <span className="font-mono text-[11px] shrink-0">
                  {line.order_reference}/{line.line_reference}
                </span>
                {/* Destinazione */}
                {line.requested_destination_display && (
                  <span className="truncate text-[11px] opacity-80">
                    {line.requested_destination_display}
                  </span>
                )}
              </div>
              {/* Qty aperta */}
              <span className="font-mono tabular-nums font-semibold shrink-0 text-[11px]">
                {fmtQty(line.open_qty)}
              </span>
            </div>
          )
        })}
      </div>
      {/* Legenda orizzonte */}
      <div className="flex items-center gap-3 mt-1.5 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-blue-200 inline-block" />
          entro orizzonte
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-amber-200 inline-block" />
          oltre orizzonte
        </span>
      </div>
    </div>
  )
}

// 4. Stock / Capienza (solo by_article)
function BloccoStockCapienza({ item }: { item: PlanningCandidateItem }) {
  if (item.planning_mode === 'by_customer_order_line') return null

  return (
    <div className="border rounded-lg p-3">
      <BlockHeader title="Stock / Capienza" />
      <div
        className="items-baseline gap-y-1.5"
        style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}
      >
        <FieldRow label="Giacenza effettiva" value={fmtQty(item.stock_effective_qty)} mono />
        <FieldRow label="Disp. netta" value={fmtQty(item.availability_qty)} mono />
        <FieldRow
          label="Headroom capienza"
          value={
            item.capacity_headroom_now_qty != null
              ? fmtQty(item.capacity_headroom_now_qty)
              : <span className="text-muted-foreground/50 italic text-xs">—</span>
          }
          mono
        />
        <FieldRow label="Supply in arrivo" value={fmtQty(item.incoming_supply_qty)} mono />
        <FieldRow
          label="Disponibilità futura"
          value={
            <span className={parseFloat(item.future_availability_qty ?? '0') < 0 ? 'text-red-600 font-semibold' : ''}>
              {fmtQty(item.future_availability_qty)}
            </span>
          }
        />
      </div>
    </div>
  )
}

// 5b. Parametri di calcolo (TASK-V2-140 + TASK-V2-141):
//     - solo by_article
//     - griglia compatta 3-col: label | value | source badge
//     - valori con unità in forma compatta (mesi, gg)
//     - CTA Override → apre pannello destra Planning/Scorte
function BloccoParametriDiCalcolo({
  item,
  detail,
  detailLoading,
  horizonDays,
  onOverride,
}: {
  item: PlanningCandidateItem
  detail: ArticoloDetail | null
  detailLoading: boolean
  horizonDays: number
  onOverride: () => void
}) {
  // Solo by_article (spec TASK-V2-140)
  if (item.planning_mode === 'by_customer_order_line') return null

  return (
    <div className="border rounded-lg p-3">
      {/* Header con CTA Override separata dalla griglia */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Parametri di calcolo
        </h3>
        <button
          type="button"
          onClick={onOverride}
          className="text-[11px] px-2.5 py-1 rounded border hover:bg-muted transition-colors font-medium"
        >
          Override
        </button>
      </div>

      {detailLoading && (
        <p className="text-xs text-muted-foreground italic">Caricamento parametri…</p>
      )}

      {!detailLoading && !detail && (
        <p className="text-xs text-muted-foreground italic">Parametri non disponibili</p>
      )}

      {!detailLoading && detail && (
        /* Griglia 3-col compatta (TASK-V2-141):
           col 1: label (max-content → allineata sul lato sinistro)
           col 2: value (max-content → incollato alla label)
           col 3: source badge (max-content → incollato al valore) */
        <div
          className="items-center gap-x-3 gap-y-1.5"
          style={{ display: 'grid', gridTemplateColumns: 'max-content max-content max-content' }}
        >
          {/* — Campi con provenienza — */}
          <span className="text-xs text-muted-foreground">Gestione scorte</span>
          <span className="text-xs font-medium">
            {detail.effective_gestione_scorte_attiva === true
              ? 'Sì'
              : detail.effective_gestione_scorte_attiva === false
              ? 'No'
              : '—'}
          </span>
          <ProvenancePill label={provenanceStockParam(detail.override_gestione_scorte_attiva, detail.famiglia_code)} />

          <span className="text-xs text-muted-foreground">Mesi scorta</span>
          <span className="text-xs font-mono tabular-nums font-medium">
            {detail.effective_stock_months != null ? `${detail.effective_stock_months} mesi` : '—'}
          </span>
          <ProvenancePill label={provenanceStockParam(detail.override_stock_months, detail.famiglia_code)} />

          <span className="text-xs text-muted-foreground">Mesi trigger</span>
          <span className="text-xs font-mono tabular-nums font-medium">
            {detail.effective_stock_trigger_months != null ? `${detail.effective_stock_trigger_months} mesi` : '—'}
          </span>
          <ProvenancePill label={provenanceStockParam(detail.override_stock_trigger_months, detail.famiglia_code)} />

          <span className="text-xs text-muted-foreground">Capienza effettiva</span>
          <span className="text-xs font-mono tabular-nums font-medium">
            {fmtQty(detail.capacity_effective_qty)}
          </span>
          <ProvenancePill label={provenanceCapacity(detail.capacity_override_qty)} />

          {/* Separatore a tutta larghezza della griglia */}
          <div className="border-t my-0.5" style={{ gridColumn: '1 / -1' }} />

          {/* — Campi derivati (read-only, nessuna provenienza) — */}
          <span className="text-xs text-muted-foreground">Qty base mensile</span>
          <span className="text-xs font-mono tabular-nums font-medium">{fmtQty(detail.monthly_stock_base_qty)}</span>
          <span />

          <span className="text-xs text-muted-foreground">Target scorta</span>
          <span className="text-xs font-mono tabular-nums font-medium">{fmtQty(detail.target_stock_qty)}</span>
          <span />

          <span className="text-xs text-muted-foreground">Trigger scorta</span>
          <span className="text-xs font-mono tabular-nums font-medium">{fmtQty(detail.trigger_stock_qty)}</span>
          <span />

          {/* Orizzonte cliente — provenienza "workspace" */}
          <span className="text-xs text-muted-foreground">Orizzonte cliente</span>
          <span className="text-xs font-mono tabular-nums font-medium">{horizonDays} gg</span>
          <ProvenancePill label="workspace" />
        </div>
      )}
    </div>
  )
}

// 6. Warnings (sempre visibile)
function BloccoWarnings({ item }: { item: PlanningCandidateItem }) {
  return (
    <div className="border rounded-lg p-3 space-y-2">
      <BlockHeader title="Warnings" />
      {item.active_warnings.length === 0 ? (
        <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded px-2 py-1">
          Nessun warning attivo
        </p>
      ) : (
        <div className="space-y-1.5">
          {item.active_warnings.map((w, idx) => (
            <div
              key={`${w.code}-${idx}`}
              className="flex items-start gap-2 p-2 rounded border bg-amber-50 border-amber-200"
            >
              <span className="font-mono text-[10px] text-amber-700 font-semibold shrink-0 mt-0.5">
                {w.code}
              </span>
              <span className="text-xs text-amber-900">{w.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// 7. Priority (sempre visibile se priority_score disponibile — TASK-V2-150, DL-ARCH-V2-044)
function BloccoPriority({ item }: { item: PlanningCandidateItem }) {
  const score = item.priority_score
  const band = item.priority_band

  if (score == null) return null

  const bandLabel =
    band === 'critical' ? 'Critico'
    : band === 'high'     ? 'Alto'
    : band === 'medium'   ? 'Medio'
    : 'Basso'

  const bandCls =
    band === 'critical' ? 'bg-red-50 text-red-700 border-red-200'
    : band === 'high'   ? 'bg-orange-50 text-orange-700 border-orange-200'
    : band === 'medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
    : 'bg-gray-50 text-gray-500 border-gray-200'

  // Derivazione delle componenti disponibili dal modello corrente (DL-ARCH-V2-044).
  // priority_components non ancora esposto come campo dedicato dal backend:
  // si ricostruisce dalla lettura dei campi gia presenti sul candidate.
  const today = new Date()
  const nearestRaw = item.nearest_delivery_date ?? item.requested_delivery_date
  let timeUrgency: number | null = null
  if (nearestRaw) {
    const ms = new Date(`${nearestRaw}T00:00:00`).getTime() - today.getTime()
    const days = Math.ceil(ms / 86_400_000)
    timeUrgency =
      days <= 7  ? 35
      : days <= 15 ? 28
      : days <= 30 ? 20
      : days <= 60 ? 10
      : 4
  }

  const shortage = parseFloat(item.customer_shortage_qty ?? '0')
  let customerPressure = 0
  if (shortage > 0) {
    customerPressure = 20 + (shortage >= 1000 ? 20 : shortage >= 500 ? 15 : shortage >= 100 ? 10 : 5)
    customerPressure = Math.min(customerPressure, 40)
  }

  const replenishment = parseFloat(item.stock_replenishment_qty ?? '0')
  const targetStock = parseFloat(item.target_stock_qty ?? '0')
  let stockPressure = 0
  if (replenishment > 0 && targetStock > 0) {
    const stockEff = parseFloat(item.stock_effective_qty ?? '0')
    const ratio = stockEff / targetStock
    stockPressure =
      ratio >= 1.0 ? 0
      : ratio >= 0.75 ? 4
      : ratio >= 0.50 ? 8
      : ratio >= 0.25 ? 14
      : ratio >= 0.0  ? 20
      : 24
  }

  const releasePenalty =
    item.release_status === 'launchable_partially'   ? 8
    : item.release_status === 'blocked_by_capacity_now' ? 18
    : 0

  const warnCount = item.active_warnings.length
  const warningPenalty =
    warnCount === 0 ? 0
    : warnCount === 1 ? 4
    : warnCount <= 3 ? 8
    : 12

  type Row = { label: string; value: number; sign: '+' | '-'; note?: string }
  const rows: Row[] = []

  if (timeUrgency != null) {
    const dayStr = nearestRaw
      ? `${Math.ceil((new Date(`${nearestRaw}T00:00:00`).getTime() - today.getTime()) / 86_400_000)} gg`
      : ''
    rows.push({ label: 'Urgenza temporale', value: timeUrgency, sign: '+', note: dayStr || undefined })
  }
  if (customerPressure > 0) {
    rows.push({ label: 'Pressione cliente', value: customerPressure, sign: '+', note: `shortage ${shortage.toFixed(0)}` })
  }
  if (stockPressure > 0) {
    rows.push({ label: 'Pressione scorta', value: stockPressure, sign: '+' })
  }
  if (releasePenalty > 0) {
    rows.push({ label: 'Penalità rilascio', value: releasePenalty, sign: '-', note: item.release_status ?? undefined })
  }
  if (warningPenalty > 0) {
    rows.push({ label: 'Penalità warning', value: warningPenalty, sign: '-', note: `${warnCount} warning` })
  }

  return (
    <div className="border rounded-lg p-3 space-y-2">
      <BlockHeader title="Priority" />

      {/* Score + band */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-xl font-bold tabular-nums text-foreground">
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-muted-foreground">/ 100</span>
        <span className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${bandCls}`}>
          {bandLabel}
        </span>
      </div>

      {/* Componenti */}
      {rows.length > 0 && (
        <div className="space-y-1 pt-1 border-t">
          {rows.map((row, i) => (
            <div key={i} className="flex items-center justify-between gap-2 text-xs">
              <span className="text-muted-foreground truncate">
                {row.label}
                {row.note && (
                  <span className="ml-1 text-[10px] text-muted-foreground/70">({row.note})</span>
                )}
              </span>
              <span className={`font-mono tabular-nums shrink-0 font-medium ${
                row.sign === '+' ? 'text-foreground' : 'text-red-600'
              }`}>
                {row.sign}{row.value}
              </span>
            </div>
          ))}
          <div className="flex items-center justify-between gap-2 text-xs border-t pt-1 mt-1">
            <span className="text-muted-foreground font-medium">Totale</span>
            <span className="font-mono tabular-nums font-bold text-foreground">{score.toFixed(0)}</span>
          </div>
        </div>
      )}

      {rows.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Nessuna componente attiva — punteggio baseline.
        </p>
      )}
    </div>
  )
}

function CenterColumn({
  item,
  detail,
  detailLoading,
  horizonDays,
  onOverride,
  onSwitchToProposal,
}: {
  item: PlanningCandidateItem | null
  detail: ArticoloDetail | null
  detailLoading: boolean
  horizonDays: number
  onOverride: () => void
  /** Porta il focus sulla scheda Proposta nella colonna destra (TASK-V2-153) */
  onSwitchToProposal: () => void
}) {
  if (!item) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Seleziona un candidate dalla lista per vedere il dettaglio.
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <BloccoIdentita item={item} />
      <BloccoClienteOrdine item={item} horizonDays={horizonDays} />
      <BloccoNeedVsRelease item={item} />
      <BloccoStockCapienza item={item} />
      {/* Parametri di calcolo (TASK-V2-140): solo by_article */}
      <BloccoParametriDiCalcolo
        item={item}
        detail={detail}
        detailLoading={detailLoading}
        horizonDays={horizonDays}
        onOverride={onOverride}
      />
      <BloccoMotivo item={item} />
      <BloccoWarnings item={item} />
      <BloccoPriority item={item} />
      {/* Switch to Proposal tab (TASK-V2-153: non apre la colonna, cambia tab) */}
      {item.proposal_status && (
        <div className="border rounded-lg p-3 flex items-center justify-between gap-2">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold">Proposta di produzione</p>
            <BackendProposalStatusBadge status={item.proposal_status} />
          </div>
          <button
            type="button"
            onClick={onSwitchToProposal}
            className="text-[11px] px-2.5 py-1 rounded border hover:bg-muted transition-colors font-medium shrink-0"
          >
            Vedi proposta →
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Right Column — badge backend proposal_status ────────────────────────────

const BACKEND_PROPOSAL_STATUS_CFG: Record<
  'Error' | 'Need review' | 'Valid for export',
  { label: string; cls: string }
> = {
  'Valid for export': { label: 'Export OK',     cls: 'bg-green-50 text-green-700 border border-green-200' },
  'Need review':      { label: 'Da verificare', cls: 'bg-amber-50 text-amber-700 border border-amber-200' },
  'Error':            { label: 'Errore',        cls: 'bg-red-50 text-red-700 border border-red-200' },
}

function BackendProposalStatusBadge({ status }: { status: 'Error' | 'Need review' | 'Valid for export' }) {
  const cfg = BACKEND_PROPOSAL_STATUS_CFG[status]
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold whitespace-nowrap ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

// ─── Right Column — pannello Proposta (TASK-V2-152) ───────────────────────────

function PannelloProposal({
  item,
  detail,
  hasScortePanel,
  onSwitchToScorte,
}: {
  item: PlanningCandidateItem
  detail: ArticoloDetail | null
  hasScortePanel: boolean
  /** Porta il focus su Planning/Scorte (TASK-V2-153: non chiude la colonna) */
  onSwitchToScorte: () => void
}) {
  const effectiveMeta = item.effective_proposal_logic_key
    ? proposalLogicMeta(item.effective_proposal_logic_key)
    : null
  const requestedMeta = item.requested_proposal_logic_key
    ? proposalLogicMeta(item.requested_proposal_logic_key)
    : null
  const hasFallback =
    item.requested_proposal_logic_key !== null &&
    item.effective_proposal_logic_key !== null &&
    item.requested_proposal_logic_key !== item.effective_proposal_logic_key

  const hasWarnings = item.proposal_local_warnings.length > 0 || item.proposal_status === 'Error' || item.proposal_status === 'Need review'

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header pannello con tab switcher (TASK-V2-153: nessun ✕, colonna sempre aperta) */}
      <div className="flex items-center border-b bg-muted/30 shrink-0">
        <button
          type="button"
          className="px-3 py-2.5 text-xs font-semibold border-b-2 border-foreground text-foreground"
        >
          Proposta
        </button>
        {hasScortePanel && (
          <button
            type="button"
            onClick={onSwitchToScorte}
            className="px-3 py-2.5 text-xs font-medium border-b-2 border-transparent text-muted-foreground hover:text-foreground transition-colors"
          >
            Planning / Scorte
          </button>
        )}
      </div>

      {/* Codice articolo */}
      <div className="px-4 py-2 border-b bg-muted/10 shrink-0">
        <span className="font-mono text-xs font-semibold text-foreground">{item.article_code}</span>
        {item.misura && (
          <span className="font-mono text-xs text-muted-foreground ml-1">– {item.misura}</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">

        {/* ── 1. Quantità + Note (TASK-V2-154) ─────────────────────────────────── */}
        <div className="border rounded-lg p-3 space-y-1.5">
          <BlockHeader title="Quantità proposta" />
          {item.proposal_qty_computed != null ? (
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-2xl font-bold tabular-nums text-foreground">
                {fmtQty(item.proposal_qty_computed)}
              </span>
              {item.misura && (
                <span className="text-xs text-muted-foreground">{item.misura}</span>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic">Quantità non calcolata</p>
          )}
          {item.note_fragment && (
            <p className="text-xs text-foreground/80 font-medium">{item.note_fragment}</p>
          )}
          {item.proposal_reason_summary && (
            <p className="text-[11px] text-muted-foreground leading-snug">{item.proposal_reason_summary}</p>
          )}
        </div>

        {/* ── 2. Descrizione + Cod. immagine (TASK-V2-154) ──────────────────────── */}
        <div className="border rounded-lg p-3 space-y-2">
          <BlockHeader title="Articolo" />
          <div
            className="items-start gap-y-1.5"
            style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}
          >
            <FieldRow
              label="Descrizione"
              value={
                <span className="text-xs leading-snug">{item.display_description || item.display_label}</span>
              }
            />
            <FieldRow
              label="Cod. immagine"
              value={
                detail?.codice_immagine
                  ? <span className="font-mono text-xs">{detail.codice_immagine}</span>
                  : <span className="text-muted-foreground/50 italic text-xs">—</span>
              }
            />
          </div>
        </div>

        {/* ── 3. Materiale + mm necessari (TASK-V2-154) ─────────────────────────── */}
        <div className="border rounded-lg p-3 space-y-2">
          <BlockHeader title="Materiale" />
          <div
            className="items-baseline gap-y-1.5"
            style={{ display: 'grid', gridTemplateColumns: 'max-content auto', columnGap: '0.75rem' }}
          >
            <FieldRow
              label="Materiale grezzo"
              value={
                detail?.materiale_grezzo_codice
                  ? <span className="font-mono text-xs">{detail.materiale_grezzo_codice}</span>
                  : <span className="text-muted-foreground/50 italic text-xs">—</span>
              }
            />
            <FieldRow
              label="Lungh. barra (mm)"
              value={
                detail?.raw_bar_length_mm
                  ? <span className="font-mono text-xs tabular-nums">{detail.raw_bar_length_mm} mm</span>
                  : <span className="text-muted-foreground/50 italic text-xs">—</span>
              }
            />
          </div>
        </div>

        {/* ── 4. Logica proposal (TASK-V2-154: spostata dopo contesto materiale) ── */}
        <div className="border rounded-lg p-3 space-y-2">
          <BlockHeader title="Logica proposal" />
          {effectiveMeta ? (
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium">{effectiveMeta.label}</span>
                {hasFallback && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                    fallback
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground">{effectiveMeta.description}</p>
              {hasFallback && requestedMeta && (
                <div className="pt-1 border-t space-y-0.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Richiesta originale
                  </p>
                  <p className="text-xs text-muted-foreground">{requestedMeta.label}</p>
                  {item.proposal_fallback_reason && (
                    <p className="text-xs text-amber-700">{item.proposal_fallback_reason}</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic">Logica non configurata</p>
          )}
        </div>

        {/* ── 5. Warnings / Diagnostica unificati (TASK-V2-154: include stato export) */}
        {hasWarnings && (
          <div className="border rounded-lg p-3 space-y-2">
            <BlockHeader title="Warnings / Diagnostica" />

            {/* Stato export — dentro il blocco unificato */}
            {item.proposal_status && item.proposal_status !== 'Valid for export' && (
              <div className="flex items-center gap-2">
                <BackendProposalStatusBadge status={item.proposal_status} />
                {item.proposal_status === 'Error' && (
                  <span className="text-xs text-muted-foreground">Blocca export XLSX</span>
                )}
              </div>
            )}

            {/* Warning locali proposta */}
            {item.proposal_local_warnings.length > 0 && (
              <div className="space-y-1">
                {item.proposal_local_warnings.map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-1.5 px-2 py-1.5 rounded border bg-amber-50 border-amber-200"
                  >
                    <span className="text-amber-500 shrink-0 text-xs leading-none mt-0.5">⚠</span>
                    <span className="text-xs text-amber-900">{w}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer azioni (V1 placeholder) */}
      <div className="border-t px-4 py-3 shrink-0 space-y-2">
        <button
          type="button"
          onClick={() => toast.info('Aggiunto al batch export (placeholder V1)')}
          className="w-full py-2 px-4 rounded-md bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Aggiungi al batch export
        </button>
        <button
          type="button"
          onClick={() => toast.info('Rimosso dal batch (placeholder V1)')}
          className="w-full py-2 px-4 rounded-md border text-sm font-medium hover:bg-muted transition-colors"
        >
          Rimuovi dal batch
        </button>
      </div>
    </div>
  )
}

// ─── Right Column — scheda Planning / Scorte (TASK-V2-140) ────────────────────

function PannelloPlanningScorte({
  articleCode,
  detail,
  onSaved,
  onClose,
  onSwitchToProposal,
}: {
  articleCode: string
  detail: ArticoloDetail
  onSaved: (updated: ArticoloDetail) => void
  onClose: () => void
  onSwitchToProposal?: () => void
}) {
  // Inizializza dallo stato corrente del dettaglio articolo
  const [planningMode, setPlanningMode] = useState<'by_article' | 'by_customer_order_line'>(
    detail.planning_mode ?? 'by_article',
  )
  const [gestioneScorteOverride, setGestioneScorteOverride] = useState<boolean | null>(
    detail.override_gestione_scorte_attiva,
  )
  const [stockMonthsRaw, setStockMonthsRaw] = useState<string>(
    detail.override_stock_months ?? '',
  )
  const [stockTriggerRaw, setStockTriggerRaw] = useState<string>(
    detail.override_stock_trigger_months ?? '',
  )
  const [capacityRaw, setCapacityRaw] = useState<string>(
    detail.capacity_override_qty ?? '',
  )
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      // 1. planning_mode → policy-override tramite override_aggrega_codice_in_produzione
      //    (derivazione: aggrega = true → by_article, false → by_customer_order_line)
      await apiClient.patch(
        `/produzione/articoli/${encodeURIComponent(articleCode)}/policy-override`,
        {
          override_considera_in_produzione: detail.override_considera_in_produzione,
          override_aggrega_codice_in_produzione: planningMode === 'by_article',
        },
      )

      // 2. gestione_scorte_attiva override
      await apiClient.patch(
        `/produzione/articoli/${encodeURIComponent(articleCode)}/gestione-scorte-override`,
        { override_gestione_scorte_attiva: gestioneScorteOverride },
      )

      // 3. stock policy override
      const stockMonths = stockMonthsRaw !== '' ? parseFloat(stockMonthsRaw) : null
      const stockTrigger = stockTriggerRaw !== '' ? parseFloat(stockTriggerRaw) : null
      const capacityQty = capacityRaw !== '' ? parseFloat(capacityRaw) : null
      await apiClient.patch(
        `/produzione/articoli/${encodeURIComponent(articleCode)}/stock-policy-override`,
        {
          override_stock_months: stockMonths !== null && !isNaN(stockMonths) ? stockMonths : null,
          override_stock_trigger_months: stockTrigger !== null && !isNaN(stockTrigger) ? stockTrigger : null,
          capacity_override_qty: capacityQty !== null && !isNaN(capacityQty) ? capacityQty : null,
        },
      )

      // Ricarica il dettaglio aggiornato
      const { data } = await apiClient.get<ArticoloDetail>(
        `/produzione/articoli/${encodeURIComponent(articleCode)}`,
      )
      onSaved(data)
      toast.success('Configurazione articolo aggiornata')
    } catch {
      toast.error('Errore durante il salvataggio configurazione')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header pannello con tab switcher */}
      <div className="flex items-center border-b bg-muted/30 shrink-0">
        {/* Tab: Proposta (se disponibile) */}
        {onSwitchToProposal && (
          <button
            type="button"
            onClick={onSwitchToProposal}
            className="px-3 py-2.5 text-xs font-medium border-b-2 border-transparent text-muted-foreground hover:text-foreground transition-colors"
          >
            Proposta
          </button>
        )}
        {/* Tab: Planning / Scorte (attivo) */}
        <button
          type="button"
          className="px-3 py-2.5 text-xs font-semibold border-b-2 border-foreground text-foreground"
        >
          Planning / Scorte
        </button>
        {/* ✕ torna alla scheda Proposta (TASK-V2-153: non chiude la colonna) */}
        <button
          type="button"
          onClick={onClose}
          className="ml-auto px-3 py-2.5 text-muted-foreground hover:text-foreground transition-colors text-sm leading-none"
          aria-label="Torna a Proposta"
          title="Torna a Proposta"
        >
          ✕
        </button>
      </div>

      {/* Codice articolo */}
      <div className="px-4 py-2 border-b bg-muted/10 shrink-0">
        <span className="font-mono text-xs font-semibold text-foreground">{articleCode}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* planning_mode */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Modalità planning
          </label>
          <div className="flex rounded-md border overflow-hidden text-xs font-medium">
            {(['by_article', 'by_customer_order_line'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setPlanningMode(mode)}
                className={`flex-1 py-2 px-2 transition-colors ${
                  planningMode === mode
                    ? 'bg-foreground text-background'
                    : 'hover:bg-muted'
                }`}
              >
                {mode === 'by_article' ? 'Per articolo' : 'Per riga ordine'}
              </button>
            ))}
          </div>
        </div>

        {/* gestione_scorte_attiva override */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Gestione scorte (override)
          </label>
          <div className="flex rounded-md border overflow-hidden text-xs font-medium">
            {([null, true, false] as const).map((val) => (
              <button
                key={String(val)}
                type="button"
                onClick={() => setGestioneScorteOverride(val)}
                className={`flex-1 py-2 transition-colors ${
                  gestioneScorteOverride === val
                    ? 'bg-foreground text-background'
                    : 'hover:bg-muted'
                }`}
              >
                {val === null ? 'Eredita' : val ? 'Sì' : 'No'}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-muted-foreground">
            Effettivo: {detail.effective_gestione_scorte_attiva === true ? 'Sì' : detail.effective_gestione_scorte_attiva === false ? 'No' : '—'}
          </p>
        </div>

        {/* stock_months override */}
        <div className="space-y-2">
          <label htmlFor="ws-stock-months" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Mesi scorta (override)
          </label>
          <input
            id="ws-stock-months"
            type="number"
            min={0}
            step={0.5}
            placeholder={detail.effective_stock_months ? `Famiglia: ${detail.effective_stock_months}` : 'Eredita dalla famiglia'}
            value={stockMonthsRaw}
            onChange={(e) => setStockMonthsRaw(e.target.value)}
            className="w-full border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {stockMonthsRaw !== '' && (
            <button
              type="button"
              onClick={() => setStockMonthsRaw('')}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Rimuovi override
            </button>
          )}
        </div>

        {/* stock_trigger_months override */}
        <div className="space-y-2">
          <label htmlFor="ws-stock-trigger" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Mesi trigger (override)
          </label>
          <input
            id="ws-stock-trigger"
            type="number"
            min={0}
            step={0.5}
            placeholder={detail.effective_stock_trigger_months ? `Famiglia: ${detail.effective_stock_trigger_months}` : 'Eredita dalla famiglia'}
            value={stockTriggerRaw}
            onChange={(e) => setStockTriggerRaw(e.target.value)}
            className="w-full border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {stockTriggerRaw !== '' && (
            <button
              type="button"
              onClick={() => setStockTriggerRaw('')}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Rimuovi override
            </button>
          )}
        </div>

        {/* capacity_override_qty */}
        <div className="space-y-2">
          <label htmlFor="ws-capacity" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Capienza override
          </label>
          <input
            id="ws-capacity"
            type="number"
            min={0}
            placeholder={detail.capacity_calculated_qty ? `Calcolata: ${fmtQty(detail.capacity_calculated_qty)}` : 'Usa capienza calcolata'}
            value={capacityRaw}
            onChange={(e) => setCapacityRaw(e.target.value)}
            className="w-full border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {capacityRaw !== '' && (
            <button
              type="button"
              onClick={() => setCapacityRaw('')}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Rimuovi override
            </button>
          )}
        </div>
      </div>

      {/* Footer salvataggio */}
      <div className="border-t px-4 py-3 shrink-0">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="w-full py-2 px-4 rounded-md bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {saving ? 'Salvataggio…' : 'Salva'}
        </button>
      </div>
    </div>
  )
}

// ─── Filter bar ───────────────────────────────────────────────────────────────

const inputCls = 'border rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring'

const SCOPE_OPTIONS: { value: ScopeFilter; label: string }[] = [
  { value: 'tutti',          label: 'Tutti' },
  { value: 'solo_clienti',   label: 'Solo clienti' },
  { value: 'solo_magazzino', label: 'Solo magazzino' },
]

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: 'priority_score', label: 'Priorità' },
  { value: 'data_consegna',  label: 'Data consegna' },
  { value: 'codice',         label: 'Codice' },
]

function WorkspaceToolbar({
  soloInProduzione,
  onSoloInProduzioneChange,
  scopeFilter,
  onScopeFilterChange,
  horizonDays,
  onHorizonDaysChange,
  filterCodice,
  onFilterCodiceChange,
  filterDesc,
  onFilterDescChange,
  filterCliente,
  onFilterClienteChange,
  famiglie,
  famigliaFilter,
  onFamigliaChange,
  sortBy,
  onSortByChange,
}: {
  soloInProduzione: boolean
  onSoloInProduzioneChange: (v: boolean) => void
  scopeFilter: ScopeFilter
  onScopeFilterChange: (v: ScopeFilter) => void
  horizonDays: number
  onHorizonDaysChange: (v: number) => void
  filterCodice: string
  onFilterCodiceChange: (v: string) => void
  filterDesc: string
  onFilterDescChange: (v: string) => void
  filterCliente: string
  onFilterClienteChange: (v: string) => void
  famiglie: string[]
  famigliaFilter: string
  onFamigliaChange: (v: string) => void
  sortBy: SortBy
  onSortByChange: (v: SortBy) => void
}) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 border-b bg-background shrink-0 flex-wrap">
      {/* Perimetro produzione */}
      <label className="flex items-center gap-1.5 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={soloInProduzione}
          onChange={(e) => onSoloInProduzioneChange(e.target.checked)}
          className="rounded"
        />
        <span className="text-xs text-muted-foreground">Solo perimetro prod.</span>
      </label>

      <div className="h-4 border-l" />

      {/* Scope filter */}
      <div className="flex items-center rounded-md border overflow-hidden text-xs font-medium">
        {SCOPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onScopeFilterChange(opt.value)}
            className={`px-2.5 py-1 transition-colors ${
              scopeFilter === opt.value
                ? 'bg-foreground text-background'
                : 'hover:bg-muted'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="h-4 border-l" />

      {/* Orizzonte cliente */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted-foreground">Orizzonte cliente</span>
        <input
          type="number"
          min={1}
          max={3650}
          value={horizonDays}
          onChange={(e) => {
            const v = parseInt(e.target.value, 10)
            if (!isNaN(v) && v >= 1) onHorizonDaysChange(v)
          }}
          className="border rounded-md px-2 py-1 text-xs w-16 text-center focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <span className="text-xs text-muted-foreground">gg</span>
      </div>

      <div className="h-4 border-l" />

      {/* Ricerche */}
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
      <input
        type="search"
        placeholder="Cliente…"
        value={filterCliente}
        onChange={(e) => onFilterClienteChange(e.target.value)}
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

      <div className="h-4 border-l" />

      {/* Sorting */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted-foreground">Ordina</span>
        <div className="flex items-center rounded-md border overflow-hidden text-xs font-medium">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onSortByChange(opt.value)}
              className={`px-2.5 py-1 transition-colors ${
                sortBy === opt.value
                  ? 'bg-foreground text-background'
                  : 'hover:bg-muted'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Surface principale ───────────────────────────────────────────────────────

export default function PlanningWorkspacePage() {
  const [items, setItems] = useState<PlanningCandidateItem[]>([])
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading')
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Filtri (TASK-V2-139)
  const [soloInProduzione, setSoloInProduzione] = useState(true)
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>('tutti')
  const [horizonDays, setHorizonDays] = useState(365)
  const [filterCodice, setFilterCodice] = useState('')
  const [filterDesc, setFilterDesc] = useState('')
  const [filterCliente, setFilterCliente] = useState('')
  const [famigliaFilter, setFamigliaFilter] = useState('')
  const [sortBy, setSortBy] = useState<SortBy>('priority_score')

  // Dettaglio articolo + pannello destra (TASK-V2-140)
  const [selectedDetail, setSelectedDetail] = useState<ArticoloDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [rightPanel, setRightPanel] = useState<RightPanel>('none')

  const loadCandidates = () => {
    setLoadStatus('loading')
    return apiClient
      .get<PlanningCandidateItem[]>('/produzione/planning-candidates')
      .then((r) => {
        setItems(r.data)
        setLoadStatus('idle')
      })
      .catch(() => {
        setLoadStatus('error')
        toast.error('Impossibile caricare i planning candidates')
      })
  }

  useEffect(() => {
    void loadCandidates()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleRefresh = async () => {
    setSyncStatus('syncing')
    try {
      await apiClient.post<SyncSurfaceResponse>('/sync/surface/produzione')
      toast.success('Dati aggiornati')
      await loadCandidates()
    } catch {
      toast.error('Errore durante il refresh')
    } finally {
      setSyncStatus('idle')
    }
  }

  const famiglie = useMemo(() => {
    const labels = items.map((i) => i.famiglia_label).filter((l): l is string => l != null)
    return [...new Set(labels)].sort()
  }, [items])

  const filtered = useMemo(() => {
    return items
      // Perimetro produzione
      .filter((i) => !soloInProduzione || i.effective_considera_in_produzione === true)
      // Scope: Solo clienti / Solo magazzino (TASK-V2-139)
      .filter((i) => {
        if (scopeFilter === 'solo_clienti')   return clienteScopeLabel(i) !== 'Magazzino'
        if (scopeFilter === 'solo_magazzino') return clienteScopeLabel(i) === 'Magazzino'
        return true
      })
      // Orizzonte cliente: filtro locale di visibilita / priorita, non di candidatura Core (TASK-V2-145).
      // Stock-only (primary_driver === 'stock', by_article): non filtrati.
      // by_article con componente cliente: usa earliest_customer_delivery_date / nearest_delivery_date.
      // by_customer_order_line: filtra per requested_delivery_date.
      .filter((i) => {
        const isStockOnly = i.primary_driver === 'stock' && i.planning_mode !== 'by_customer_order_line'
        if (isStockOnly) return true
        const requestedDate =
          i.planning_mode === 'by_customer_order_line'
            ? i.requested_delivery_date
            : resolveRequestedDate(i) ?? i.nearest_delivery_date
        if (!requestedDate) return true
        const d = new Date(`${requestedDate}T00:00:00`)
        const horizon = new Date()
        horizon.setHours(0, 0, 0, 0)
        horizon.setDate(horizon.getDate() + horizonDays)
        return d <= horizon
      })
      // Ricerche (TASK-V2-139)
      .filter((i) => matchesCodice(i, filterCodice))
      .filter((i) => matchesDesc(i, filterDesc))
      .filter((i) => matchesCliente(i, filterCliente))
      .filter((i) => !famigliaFilter || i.famiglia_label === famigliaFilter)
      // Sorting (TASK-V2-139, TASK-V2-149)
      .sort((a, b) => {
        if (sortBy === 'codice') {
          return a.article_code.localeCompare(b.article_code)
        }
        if (sortBy === 'priority_score') {
          // Descending: score piu alto = piu urgente. Nulls last.
          const sa = a.priority_score ?? -1
          const sb = b.priority_score ?? -1
          if (sa !== sb) return sb - sa
          return a.article_code.localeCompare(b.article_code)
        }
        // data_consegna: nulls last, secondary sort per codice (stabilità)
        const da = resolveRequestedDate(a)
        const db = resolveRequestedDate(b)
        const ta = da ? new Date(`${da}T00:00:00`).getTime() : Infinity
        const tb = db ? new Date(`${db}T00:00:00`).getTime() : Infinity
        if (ta !== tb) return ta - tb
        return a.article_code.localeCompare(b.article_code)
      })
  }, [items, soloInProduzione, scopeFilter, horizonDays, filterCodice, filterDesc, filterCliente, famigliaFilter, sortBy])

  const selectedItem = useMemo(
    () => filtered.find((i) => i.source_candidate_id === selectedId) ?? null,
    [filtered, selectedId],
  )

  // Carica ArticoloDetail quando cambia l'articolo selezionato (TASK-V2-140, TASK-V2-153)
  useEffect(() => {
    if (!selectedItem) {
      setSelectedDetail(null)
      setRightPanel('none')
      return
    }
    // Nuovo articolo selezionato: torna sempre su Proposta (TASK-V2-153)
    setRightPanel('proposal')
    setDetailLoading(true)
    setSelectedDetail(null)
    apiClient
      .get<ArticoloDetail>(`/produzione/articoli/${encodeURIComponent(selectedItem.article_code)}`)
      .then((r) => setSelectedDetail(r.data))
      .catch(() => { /* silent: BloccoParametriDiCalcolo mostra "non disponibile" */ })
      .finally(() => setDetailLoading(false))
  }, [selectedItem?.article_code]) // eslint-disable-line react-hooks/exhaustive-deps

  // Seleziona un candidate: aggiorna centro e destra immediatamente (TASK-V2-153)
  const handleSelectCandidate = (id: string) => {
    setSelectedId(id)
    setRightPanel('proposal')
  }

  const busy = loadStatus === 'loading' || syncStatus === 'syncing'

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/30 text-xs text-muted-foreground shrink-0">
        <span className="font-medium text-foreground">Planning Workspace</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded border bg-background text-muted-foreground">
          shadow view
        </span>

        {loadStatus === 'idle' && (
          <span className={`px-2 py-0.5 rounded font-medium ${
            filtered.length > 0 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
          }`}>
            {filtered.length > 0
              ? `${filtered.length} candidat${filtered.length === 1 ? 'o' : 'i'}`
              : 'Nessun candidate'}
          </span>
        )}
        {loadStatus === 'error' && (
          <span className="px-2 py-0.5 rounded font-medium bg-red-100 text-red-700">
            Errore caricamento
          </span>
        )}

        <button
          onClick={handleRefresh}
          disabled={busy}
          className="ml-auto py-1 px-3 border rounded-md text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
        >
          {syncStatus === 'syncing' ? 'Aggiornamento…' : loadStatus === 'loading' ? 'Caricamento…' : 'Aggiorna dati'}
        </button>
      </div>

      {/* Loading / Error fullscreen */}
      {loadStatus === 'loading' && (
        <div className="flex items-center justify-center flex-1 text-sm text-muted-foreground">
          Caricamento…
        </div>
      )}
      {loadStatus === 'error' && (
        <div className="flex items-center justify-center flex-1 text-sm text-red-600">
          Impossibile caricare i dati. Riprovare.
        </div>
      )}

      {/* Layout principale: toolbar + colonne */}
      {loadStatus === 'idle' && (
        <div className="flex flex-col flex-1 overflow-hidden">
          <WorkspaceToolbar
            soloInProduzione={soloInProduzione}
            onSoloInProduzioneChange={setSoloInProduzione}
            scopeFilter={scopeFilter}
            onScopeFilterChange={setScopeFilter}
            horizonDays={horizonDays}
            onHorizonDaysChange={setHorizonDays}
            filterCodice={filterCodice}
            onFilterCodiceChange={setFilterCodice}
            filterDesc={filterDesc}
            onFilterDescChange={setFilterDesc}
            filterCliente={filterCliente}
            onFilterClienteChange={setFilterCliente}
            famiglie={famiglie}
            famigliaFilter={famigliaFilter}
            onFamigliaChange={setFamigliaFilter}
            sortBy={sortBy}
            onSortByChange={setSortBy}
          />

          {/* Colonne */}
          <div className="flex flex-1 overflow-hidden">
            {/* Colonna sinistra — inbox sintetica */}
            <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
              <div className="px-3 py-2 border-b bg-muted/30 shrink-0">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Candidates
                </span>
              </div>
              <LeftColumn
                items={filtered}
                selectedId={selectedId}
                onSelect={handleSelectCandidate}
              />
            </div>

            {/* Colonna centrale — dettaglio (larghezza fissa: 3-col sempre attivo TASK-V2-153) */}
            <div className="w-[46%] shrink-0 border-r overflow-hidden">
              <CenterColumn
                item={selectedItem}
                detail={selectedDetail}
                detailLoading={detailLoading}
                horizonDays={horizonDays}
                onOverride={() => {
                  if (selectedDetail) setRightPanel('planning_scorte')
                }}
                onSwitchToProposal={() => setRightPanel('proposal')}
              />
            </div>

            {/* Colonna destra — sempre presente (TASK-V2-153): placeholder | Proposta | Planning/Scorte */}
            <div className="flex-1 border-l overflow-hidden">
              {!selectedItem && (
                <div className="flex items-center justify-center h-full text-xs text-muted-foreground p-4 text-center">
                  Seleziona un candidate dalla lista per vedere la proposta.
                </div>
              )}
              {selectedItem && rightPanel === 'proposal' && (
                <PannelloProposal
                  item={selectedItem}
                  detail={selectedDetail}
                  hasScortePanel={selectedDetail != null}
                  onSwitchToScorte={() => {
                    if (selectedDetail) setRightPanel('planning_scorte')
                  }}
                />
              )}
              {selectedItem && rightPanel === 'planning_scorte' && selectedDetail && (
                <PannelloPlanningScorte
                  articleCode={selectedItem.article_code}
                  detail={selectedDetail}
                  onSaved={(updated) => setSelectedDetail(updated)}
                  onClose={() => setRightPanel('proposal')}
                  onSwitchToProposal={() => setRightPanel('proposal')}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
