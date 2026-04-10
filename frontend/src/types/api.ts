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
