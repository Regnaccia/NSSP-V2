import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'

/** Placeholder superficie Logistica — da implementare nei task successivi. */
export default function LogisticaHome() {
  const navigate = useNavigate()
  const { username, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-6 py-3 flex items-center justify-between">
        <span className="font-semibold">Logistica</span>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>{username}</span>
          <button onClick={handleLogout} className="hover:text-foreground transition-colors">
            Esci
          </button>
        </div>
      </header>
      <main className="p-8 text-center text-muted-foreground">
        Superficie Logistica — da implementare
      </main>
    </div>
  )
}
