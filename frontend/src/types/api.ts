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
