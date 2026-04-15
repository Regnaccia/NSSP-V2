/**
 * Tipi che rispecchiano il contratto del backend V2.
 * Derivati da app/schemas/auth.py (DL-ARCH-V2-004).
 */

export interface Surface {
  role: string
  path: string
  label: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
  roles: string[]
  access_mode: string
  available_surfaces: Surface[]
}

export interface SessionResponse {
  user_id: number
  username: string
  roles: string[]
  access_mode: string
  available_surfaces: Surface[]
}

// ─── Sync on demand (DL-ARCH-V2-011) ────────────────────────────────────────

export interface EntityRunResult {
  entity_code: string
  status: 'success' | 'error' | 'skipped'
  run_id: string | null
  rows_seen: number
  rows_written: number
  rows_deleted: number
  error_message: string | null
  started_at: string
  finished_at: string | null
}

export interface SyncSurfaceResponse {
  triggered_at: string
  results: EntityRunResult[]
}

export interface EntityFreshness {
  entity_code: string
  last_success_at: string | null
  last_status: string | null
  is_stale: boolean
}

export interface FreshnessResponse {
  entities: EntityFreshness[]
  surface_ready: boolean
}

// ─── Core slice clienti + destinazioni (DL-ARCH-V2-010) ──────────────────────

/** Dato Easy read-only */
export interface ClienteItem {
  codice_cli: string
  ragione_sociale: string
}

/** Riga destinazione per il cliente selezionato */
export interface DestinazioneItem {
  // Dati Easy read-only
  codice_destinazione: string
  codice_cli: string | null
  numero_progressivo_cliente: string | null
  indirizzo: string | null
  citta: string | null
  provincia: string | null
  // Dato interno configurabile
  nickname_destinazione: string | null
  // Campo sintetico derivato dal Core
  display_label: string
  // True se destinazione principale derivata da ANACLI (DL-ARCH-V2-012)
  is_primary: boolean
}

// ─── Core slice articoli (DL-ARCH-V2-013) ────────────────────────────────────

/** Voce catalogo famiglie articolo — picker (solo attive) */
export interface FamigliaItem {
  code: string
  label: string
  sort_order: number | null
  /** Flag abilitazione configurazione campo barra (TASK-V2-123) */
  raw_bar_length_mm_enabled: boolean
}

/** Riga tabella gestione famiglie — tutte, con conteggio articoli */
export interface FamigliaRow {
  code: string
  label: string
  sort_order: number | null
  is_active: boolean
  considera_in_produzione: boolean
  aggrega_codice_in_produzione: boolean
  n_articoli: number
  /** Stock policy defaults V1 — null se non configurati (TASK-V2-093) */
  stock_months: string | null
  stock_trigger_months: string | null
  /** Flag esplicito di applicabilita stock policy (TASK-V2-096) */
  gestione_scorte_attiva: boolean
  /** Flag abilitazione configurazione campo lunghezza barra grezza (TASK-V2-118) */
  raw_bar_length_mm_enabled: boolean
}

/** Riga di lista articoli */
export interface ArticoloItem {
  codice_articolo: string
  descrizione_1: string | null
  descrizione_2: string | null
  unita_misura_codice: string | null
  display_label: string
  famiglia_code: string | null
  famiglia_label: string | null
}

/** Dettaglio completo dell'articolo selezionato */
export interface ArticoloDetail {
  codice_articolo: string
  descrizione_1: string | null
  descrizione_2: string | null
  unita_misura_codice: string | null
  source_modified_at: string | null
  categoria_articolo_1: string | null
  materiale_grezzo_codice: string | null
  quantita_materiale_grezzo_occorrente: string | null
  quantita_materiale_grezzo_scarto: string | null
  misura_articolo: string | null
  codice_immagine: string | null
  contenitori_magazzino: string | null
  peso_grammi: string | null
  display_label: string
  famiglia_code: string | null
  famiglia_label: string | null
  /** Giacenza netta canonica (DL-ARCH-V2-016) — null se nessun movimento registrato */
  on_hand_qty: string | null
  /** Timestamp del calcolo giacenza */
  giacenza_computed_at: string | null
  /** Quota appartata per cliente DOC_QTAP (DL-ARCH-V2-019) — null se nessuna quota appartata */
  customer_set_aside_qty: string | null
  /** Timestamp del calcolo set aside */
  set_aside_computed_at: string | null
  /** Impegni totali (customer_order + production) (DL-ARCH-V2-017) — null se nessun impegno */
  committed_qty: string | null
  /** Timestamp del calcolo commitments */
  commitments_computed_at: string | null
  /** Disponibilita canonica (DL-ARCH-V2-021) — null se fact non ancora calcolato */
  availability_qty: string | null
  /** Timestamp del calcolo availability */
  availability_computed_at: string | null
  /** Planning policy effettive (DL-ARCH-V2-026, TASK-V2-064) — null se senza famiglia e senza override */
  effective_considera_in_produzione: boolean | null
  effective_aggrega_codice_in_produzione: boolean | null
  /** Override articolo (DL-ARCH-V2-026, TASK-V2-067) — null = eredita default famiglia */
  override_considera_in_produzione: boolean | null
  override_aggrega_codice_in_produzione: boolean | null
  /** Gestione scorte attiva — effective e override articolo (TASK-V2-096, TASK-V2-098) */
  effective_gestione_scorte_attiva: boolean | null
  override_gestione_scorte_attiva: boolean | null
  /** Vocabolario esplicito planning_mode (DL-ARCH-V2-027, TASK-V2-069) */
  planning_mode: PlanningMode | null
  /** Stock policy effettiva V1 (DL-ARCH-V2-030, TASK-V2-083) — null se non configurata */
  effective_stock_months: string | null
  effective_stock_trigger_months: string | null
  /** Override stock policy articolo-specifici (TASK-V2-089) — null = eredita famiglia */
  override_stock_months: string | null
  override_stock_trigger_months: string | null
  /** Capacity override articolo-specifica — null se non impostata */
  capacity_override_qty: string | null
  /** Metriche stock calcolate — null se planning_mode != by_article o dati insufficienti */
  monthly_stock_base_qty: string | null
  capacity_calculated_qty: string | null
  capacity_effective_qty: string | null
  target_stock_qty: string | null
  trigger_stock_qty: string | null
  stock_computed_at: string | null
  stock_strategy_key: string | null
  effective_proposal_logic_key: string | null
  proposal_logic_key: string | null
  proposal_logic_article_params: Record<string, unknown>
  /** Lunghezza barra grezza in mm — null se non configurata (TASK-V2-118) */
  raw_bar_length_mm: string | null
}

// ─── Core slice produzioni (DL-ARCH-V2-015) ──────────────────────────────────

/** Risposta paginata della lista produzioni (TASK-V2-034) */
export interface ProduzioniPaginata {
  items: ProduzioneItem[]
  total: number
  limit: number
  offset: number
}

/** Produzione aggregata (attiva o storica) con bucket e stato computato */
export interface ProduzioneItem {
  id_dettaglio: number
  bucket: 'active' | 'historical'
  cliente_ragione_sociale: string | null
  codice_articolo: string | null
  descrizione_articolo: string | null
  numero_documento: string | null
  numero_riga_documento: number | null
  quantita_ordinata: string | null
  quantita_prodotta: string | null
  stato_produzione: 'attiva' | 'completata'
  forza_completata: boolean
}

// ─── Core slice criticita articoli (DL-ARCH-V2-023, TASK-V2-055) ─────────────

/** Articolo critico V1: availability_qty < 0 */
export interface CriticitaItem {
  article_code: string
  descrizione_1: string | null
  descrizione_2: string | null
  display_label: string
  famiglia_code: string | null
  famiglia_label: string | null
  inventory_qty: string
  customer_set_aside_qty: string
  committed_qty: string
  availability_qty: string
  computed_at: string
}

// ─── Core slice planning candidates (DL-ARCH-V2-025, TASK-V2-062, TASK-V2-065, TASK-V2-069, TASK-V2-071, TASK-V2-074) ─

/** Vocabolario esplicito planning_mode (DL-ARCH-V2-027, TASK-V2-069) */
export type PlanningMode = 'by_article' | 'by_customer_order_line'
export type PlanningPrimaryDriver = 'customer' | 'stock'
export interface PlanningActiveWarningItem {
  code: string
  severity: string
  message: string
}

/** Planning candidate — by_article (V1) o by_customer_order_line (V2, TASK-V2-071, TASK-V2-074) */
export interface PlanningCandidateItem {
  source_candidate_id: string
  article_code: string
  /** Campo sintetico di presentazione */
  display_label: string
  famiglia_code: string | null
  famiglia_label: string | null
  /** Planning policy effettive (DL-ARCH-V2-026) — null se articolo senza famiglia e senza override */
  effective_considera_in_produzione: boolean | null
  effective_aggrega_codice_in_produzione: boolean | null
  /** Vocabolario esplicito planning_mode (DL-ARCH-V2-027, TASK-V2-069) */
  planning_mode: PlanningMode | null
  /** Codice reason esplicito della candidatura (DL-ARCH-V2-028 §4) */
  reason_code: string
  /** Testo leggibile della reason (DL-ARCH-V2-028 §4) */
  reason_text: string
  /** Segmenti descrittivi canonici unificati (TASK-V2-110) */
  description_parts: string[]
  /** Descrizione di presentazione canonica derivata da description_parts */
  display_description: string
  /** Warning attivi articolo visibili all'utente corrente (TASK-V2-111) */
  active_warning_codes: string[]
  active_warnings: PlanningActiveWarningItem[]
  /** Unità di misura / misura articolo (DL-ARCH-V2-028 §3) — null se non disponibile */
  misura: string | null
  /** abs del deficit — fabbisogno minimo in entrambe le modalità */
  required_qty_minimum: string
  primary_driver: PlanningPrimaryDriver | null
  requested_destination_display: string | null
  computed_at: string

  // ─── by_article (null per by_customer_order_line) ────────────────────────
  /** Quota libera effettiva = max(on_hand,0) - set_aside - committed — null per by_customer_order_line */
  availability_qty: string | null
  /** Domanda cliente aggregata per articolo — null per by_customer_order_line */
  customer_open_demand_qty: string | null
  /** Supply aggregata da produzioni attive — null per by_customer_order_line */
  incoming_supply_qty: string | null
  /** availability + incoming_supply — null per by_customer_order_line */
  future_availability_qty: string | null
  /** Componente shortage cliente = max(-fav, 0) — null se no stock policy o by_customer_order_line */
  customer_shortage_qty: string | null
  /** Componente replenishment scorta = max(target - max(fav,0), 0) — null se no stock policy o by_customer_order_line */
  stock_replenishment_qty: string | null
  /** Totale = customer_shortage + stock_replenishment — null se no stock policy o by_customer_order_line */
  required_qty_total: string | null
  /** True se data_consegna più vicina ≤ today + customer_horizon_days. Null se nessuna data o by_customer_order_line */
  is_within_customer_horizon: boolean | null
  earliest_customer_delivery_date: string | null
  /** Data_consegna più vicina (ISO date string) tra le righe ordine. Null se nessuna data o by_customer_order_line */
  nearest_delivery_date: string | null

  // ─── by_customer_order_line (null per by_article) ────────────────────────
  /** Numero ordine cliente — null per by_article */
  order_reference: string | null
  /** Numero riga ordine cliente — null per by_article */
  line_reference: number | null
  /** Descrizione dalla riga ordine cliente (DL-ARCH-V2-028 §2) — null per by_article */
  order_line_description: string | null
  full_order_line_description: string | null
  requested_delivery_date: string | null
  /** max(ordered - set_aside - fulfilled, 0) per la riga — null per by_article */
  line_open_demand_qty: string | null
  /** Supply da produzioni collegate a questa riga — null per by_article */
  linked_incoming_supply_qty: string | null
  /** linked_supply - line_demand (negativa se candidate) — null per by_article */
  line_future_coverage_qty: string | null
}

/** Dettaglio completo della destinazione selezionata */
export interface DestinazioneDetail {
  // Dati Easy read-only — destinazione
  codice_destinazione: string
  codice_cli: string | null
  numero_progressivo_cliente: string | null
  indirizzo: string | null
  citta: string | null
  provincia: string | null
  nazione_codice: string | null
  telefono_1: string | null
  // Dato Easy read-only — da cliente (join)
  ragione_sociale_cliente: string | null
  // Dato interno configurabile
  nickname_destinazione: string | null
  // Campo sintetico
  display_label: string
  // True se destinazione principale derivata da ANACLI (DL-ARCH-V2-012)
  is_primary: boolean
}


// ─── Core slice warnings (DL-ARCH-V2-029, TASK-V2-076, TASK-V2-077, TASK-V2-078, TASK-V2-081) ─

/** Warning canonico — shape minima V1 */
export interface WarningItem {
  warning_id: string
  type: string
  severity: string
  entity_type: string
  entity_key: string
  message: string
  source_module: string
  /** Aree/reparti operativi abilitati — governa badge nei moduli operativi (TASK-V2-081) */
  visible_to_areas: string[]
  created_at: string
  // Campi specifici NEGATIVE_STOCK
  article_code: string
  stock_calculated: string
  anomaly_qty: string
}

/** Configurazione visibilita per un tipo warning — governata da admin */
export interface WarningTypeConfigItem {
  warning_type: string
  /** Aree/reparti operativi (magazzino, produzione, logistica) — TASK-V2-081 */
  visible_to_areas: string[]
  /** True se nessuna riga in DB — si usa il default del tipo */
  is_default: boolean
  /** null quando is_default=true */
  updated_at: string | null
}

// ─── Production Proposals V1 ─────────────────────────────────────────────────

export type ProductionProposalWorkflowStatus =
  | 'exported'
  | 'reconciled'
  | 'cancelled'

export type ProposalWorkspaceStatus = 'open' | 'exported' | 'abandoned'

export interface ProposalWorkspaceRowItem {
  row_id: number
  source_candidate_id: string
  planning_mode: string | null
  article_code: string
  display_label: string
  display_description: string
  primary_driver: PlanningPrimaryDriver | null
  required_qty_minimum: string
  required_qty_total: string
  customer_shortage_qty: string | null
  stock_replenishment_qty: string | null
  requested_delivery_date: string | null
  requested_destination_display: string | null
  active_warning_codes: string[]
  proposal_logic_key: string
  proposed_qty: string
  override_qty: string | null
  override_reason: string | null
  final_qty: string
  order_reference: string | null
  line_reference: number | null
  computed_at: string
  updated_at: string
  // ─── Campi export-preview (TASK-V2-115) ──────────────────────────────────
  description_parts: string[]
  export_description: string
  codice_immagine: string | null
  materiale: string | null
  mm_materiale: string | null
  ordine: string | null
  ordine_linea_mancante: boolean
  note_preview: string
  user_preview: string
}

export interface ProposalWorkspaceDetail {
  workspace_id: string
  status: ProposalWorkspaceStatus
  created_at: string
  expires_at: string
  updated_at: string
  rows: ProposalWorkspaceRowItem[]
}

export interface ProposalWorkspaceGenerateResult {
  workspace_id: string
  created_count: number
  skipped_missing_count: number
  workspace_row_count: number
}

export interface ProductionProposalItem {
  proposal_id: number
  source_candidate_id: string
  workspace_id: string | null
  workspace_row_id: number | null
  planning_mode: string | null
  article_code: string
  display_label: string
  display_description: string
  primary_driver: PlanningPrimaryDriver | null
  required_qty_minimum: string
  required_qty_total: string
  customer_shortage_qty: string | null
  stock_replenishment_qty: string | null
  requested_delivery_date: string | null
  requested_destination_display: string | null
  active_warning_codes: string[]
  proposal_logic_key: string
  proposed_qty: string
  override_qty: string | null
  override_reason: string | null
  final_qty: string
  workflow_status: ProductionProposalWorkflowStatus
  ode_ref: string
  export_batch_id: string | null
  reconciled_production_bucket: string | null
  reconciled_production_id_dettaglio: number | null
  order_reference: string | null
  line_reference: number | null
  computed_at: string
  updated_at: string
  // ─── Campi export-preview (TASK-V2-115) ──────────────────────────────────
  description_parts: string[]
  export_description: string
  codice_immagine: string | null
  materiale: string | null
  mm_materiale: string | null
  ordine: string | null
  ordine_linea_mancante: boolean
  note_preview: string
  user_preview: string
}

export interface ProductionProposalDetail extends ProductionProposalItem {
  proposal_logic_params_snapshot: Record<string, unknown>
  created_at: string
}

export interface ProductionProposalReconcileResult {
  matched: number
  unmatched: number
  scanned: number
  reconciled_at: string
}

export interface ProposalLogicConfigResponse {
  default_logic_key: string
  logic_params_by_key: Record<string, Record<string, unknown>>
  is_default: boolean
  updated_at: string | null
  known_logics: string[]
}
