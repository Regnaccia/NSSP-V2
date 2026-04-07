import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'

/** Placeholder superficie Admin — da implementare nei task successivi. */
export default function AdminHome() {
  const navigate = useNavigate()
  const { username, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-6 py-3 flex items-center justify-between">
        <span className="font-semibold">Admin</span>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>{username}</span>
          <button onClick={handleLogout} className="hover:text-foreground transition-colors">
            Esci
          </button>
        </div>
      </header>
      <main className="p-8 text-center text-muted-foreground">
        Superficie Admin — da implementare
      </main>
    </div>
  )
}
