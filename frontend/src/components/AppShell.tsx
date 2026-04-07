import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'

/**
 * Layout shell applicativo persistente (DL-UIX-V2-001).
 *
 * - Sidebar con voci di navigazione derivate da `available_surfaces`
 * - <Outlet /> per il contenuto della surface attiva
 * - Header utente e logout centralizzati
 *
 * Le singole surface non devono più includere header o logout propri.
 */
export default function AppShell() {
  const navigate = useNavigate()
  const { username, available_surfaces, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-48 border-r flex flex-col shrink-0">
        {/* Brand */}
        <div className="px-4 py-4 border-b">
          <span className="font-bold text-sm tracking-wide">ODE OMR</span>
        </div>

        {/* Navigazione superfici */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {available_surfaces.map((s) => (
            <NavLink
              key={s.role}
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
          ))}
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
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  )
}
