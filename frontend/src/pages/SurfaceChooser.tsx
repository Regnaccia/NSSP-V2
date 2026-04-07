import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'
import type { Surface } from '@/types/api'

/**
 * Pagina di scelta superficie per utenti con più ruoli.
 *
 * Mostrata solo quando available_surfaces.length > 1.
 * Il routing è guidato dalle superfici restituite dal backend (DL-ARCH-V2-004 §7).
 */
export default function SurfaceChooser() {
  const navigate = useNavigate()
  const { username, available_surfaces } = useAuthStore()

  const handleSelect = (surface: Surface) => {
    navigate(surface.path, { replace: true })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <div className="w-full max-w-md space-y-6 p-8 bg-background border rounded-xl shadow-sm">
        <div className="text-center space-y-1">
          <h1 className="text-xl font-bold tracking-tight">Benvenuto, {username}</h1>
          <p className="text-sm text-muted-foreground">Scegli la superficie di lavoro</p>
        </div>

        <div className="grid gap-3">
          {available_surfaces.map((surface) => (
            <button
              key={surface.role}
              onClick={() => handleSelect(surface)}
              className="w-full py-4 px-6 bg-card border rounded-lg text-left hover:border-primary hover:bg-muted/50 transition-colors group"
            >
              <span className="font-medium group-hover:text-primary transition-colors">
                {surface.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
