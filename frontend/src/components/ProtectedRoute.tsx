import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'

interface Props {
  children: React.ReactNode
  /** Se specificato, verifica che l'utente abbia almeno uno di questi ruoli. */
  roles?: string[]
}

/**
 * Wrapper route che richiede autenticazione valida.
 *
 * Se l'utente non è autenticato → redirect a /login.
 * Se è specificato `roles` e l'utente non ha nessuno dei ruoli richiesti → redirect a /.
 *
 * Nota: il controllo effettivo dei permessi è sempre backend.
 * Questo componente serve solo a proteggere la navigazione UI.
 */
export function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, roles: userRoles } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (roles && !roles.some((r) => userRoles.includes(r))) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
