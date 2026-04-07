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
