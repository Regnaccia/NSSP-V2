/**
 * Auth store V2.
 *
 * Differenze rispetto a V1:
 * - roles: string[]  (non ruolo singolo)
 * - available_surfaces: Surface[]  (calcolate dal backend)
 * - access_mode: string  (sempre "browser" in questo slice)
 *
 * Il backend è fonte di verità per ruoli e superfici (DL-ARCH-V2-004 §8).
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Surface } from '@/types/api'

interface AuthState {
  token: string | null
  user_id: number | null
  username: string | null
  roles: string[]
  access_mode: string | null
  available_surfaces: Surface[]
  isAuthenticated: boolean
  login: (session: {
    token: string
    user_id: number
    username: string
    roles: string[]
    access_mode: string
    available_surfaces: Surface[]
  }) => void
  updateSurfaces: (surfaces: Surface[]) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user_id: null,
      username: null,
      roles: [],
      access_mode: null,
      available_surfaces: [],
      isAuthenticated: false,
      login: (session) =>
        set({
          token: session.token,
          user_id: session.user_id,
          username: session.username,
          roles: session.roles,
          access_mode: session.access_mode,
          available_surfaces: session.available_surfaces,
          isAuthenticated: true,
        }),
      updateSurfaces: (surfaces) => set({ available_surfaces: surfaces }),
      logout: () =>
        set({
          token: null,
          user_id: null,
          username: null,
          roles: [],
          access_mode: null,
          available_surfaces: [],
          isAuthenticated: false,
        }),
    }),
    { name: 'ode-auth-v2' }
  )
)
