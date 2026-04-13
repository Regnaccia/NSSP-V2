import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'

/**
 * Layout shell applicativo persistente (DL-UIX-V2-001).
 *
 * - Sidebar con voci di navigazione derivate da `available_surfaces`
 * - Navigazione contestuale per-surface (DL-UIX-V2-003): secondo livello
 *   frontend-defined, visibile solo sulla surface attiva
 * - <Outlet /> per il contenuto della surface attiva
 * - Header utente e logout centralizzati
 *
 * Le singole surface non devono più includere header o logout propri.
 */

// ─── Mappatura frontend-defined: surface role → funzioni contestuali ──────────
//
// Il livello primario (surface) deriva da `available_surfaces` (backend).
// Il livello secondario (funzioni) è frontend-defined nel primo slice (DL-UIX-V2-003 §3).
//
// Estendere qui quando si aggiungono nuove funzioni a una surface.

interface SurfaceFunction {
  path: string
  label: string
}

const SURFACE_FUNCTIONS: Record<string, SurfaceFunction[]> = {
  admin: [
    { path: '/admin/utenti', label: 'Utenti' },
  ],
  logistica: [
    { path: '/logistica/clienti-destinazioni', label: 'Clienti / Destinazioni' },
  ],
  produzione: [
    { path: '/produzione/articoli', label: 'Articoli' },
    { path: '/produzione/famiglie', label: 'Famiglie' },
    { path: '/produzione/produzioni', label: 'Produzioni' },
    { path: '/produzione/criticita', label: 'Criticità' },
    { path: '/produzione/planning-candidates', label: 'Planning' },
  ],
}

// ─── AppShell ─────────────────────────────────────────────────────────────────

export default function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { username, available_surfaces, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-48 border-r flex flex-col shrink-0">
        {/* Brand */}
        <div className="px-4 py-4 border-b">
          <span className="font-bold text-sm tracking-wide">ODE OMR</span>
        </div>

        {/* Navigazione superfici + contestuale */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {available_surfaces.map((s) => {
            // Rileva se la surface corrente è quella attiva
            const isActiveSurface =
              location.pathname === s.path ||
              location.pathname.startsWith(s.path + '/')

            const contextualFunctions = SURFACE_FUNCTIONS[s.role] ?? []

            return (
              <div key={s.role}>
                {/* Livello primario: surface */}
                <NavLink
                  to={s.path}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    }`
                  }
                >
                  {s.label}
                </NavLink>

                {/* Livello secondario: funzioni contestuali — visibili solo sulla surface attiva */}
                {isActiveSurface && contextualFunctions.length > 0 && (
                  <div className="ml-2 mt-0.5 space-y-0.5">
                    {contextualFunctions.map((fn) => (
                      <NavLink
                        key={fn.path}
                        to={fn.path}
                        end
                        className={({ isActive }) =>
                          `block px-3 py-1.5 rounded-md text-xs transition-colors ${
                            isActive
                              ? 'text-foreground font-semibold bg-muted'
                              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                          }`
                        }
                      >
                        {fn.label}
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* Footer utente */}
        <div className="border-t px-4 py-3 space-y-1">
          <p className="text-xs text-muted-foreground truncate">{username}</p>
          <button
            onClick={handleLogout}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Esci
          </button>
        </div>
      </aside>

      {/* Contenuto surface */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}
