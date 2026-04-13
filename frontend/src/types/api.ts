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
  /** Vocabolario esplicito planning_mode (DL-ARCH-V2-027, TASK-V2-069) */
  planning_mode: PlanningMode | null
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

// ─── Core slice planning candidates (DL-ARCH-V2-025, TASK-V2-062, TASK-V2-065, TASK-V2-069, TASK-V2-071) ─

/** Vocabolario esplicito planning_mode (DL-ARCH-V2-027, TASK-V2-069) */
export type PlanningMode = 'by_article' | 'by_customer_order_line'

/** Planning candidate — by_article (V1) o by_customer_order_line (V2, TASK-V2-071) */
export interface PlanningCandidateItem {
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
  /** abs del deficit — fabbisogno minimo in entrambe le modalità */
  required_qty_minimum: string
  computed_at: string

  // ─── by_article (null per by_customer_order_line) ────────────────────────
  /** Quota libera attuale (core_availability) — null per by_customer_order_line */
  availability_qty: string | null
  /** Domanda cliente aggregata per articolo — null per by_customer_order_line */
  customer_open_demand_qty: string | null
  /** Supply aggregata da produzioni attive — null per by_customer_order_line */
  incoming_supply_qty: string | null
  /** availability + incoming_supply — null per by_customer_order_line */
  future_availability_qty: string | null

  // ─── by_customer_order_line (null per by_article) ────────────────────────
  /** Numero ordine cliente — null per by_article */
  order_reference: string | null
  /** Numero riga ordine cliente — null per by_article */
  line_reference: number | null
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
