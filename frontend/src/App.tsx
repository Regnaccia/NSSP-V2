import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'
import AppShell from '@/components/AppShell'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import Login from '@/pages/Login'
import SurfaceChooser from '@/pages/SurfaceChooser'
import AdminHome from '@/pages/surfaces/AdminHome'
import LogisticaHome from '@/pages/surfaces/LogisticaHome'
import MagazzinoHome from '@/pages/surfaces/MagazzinoHome'
import ProduzioneHome from '@/pages/surfaces/ProduzioneHome'

/**
 * Redirect iniziale dopo login (DL-UIX-V2-001 §4).
 *
 * - 0 superfici → /login
 * - 1 o più superfici → prima superficie disponibile (no chooser come percorso standard)
 */
function HomeRedirect() {
  const surfaces = useAuthStore((s) => s.available_surfaces)

  if (surfaces.length === 0) {
    return <Navigate to="/login" replace />
  }
  return <Navigate to={surfaces[0].path} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Pubblica */}
        <Route path="/login" element={<Login />} />

        {/* Chooser — mantenuto come fallback tecnico, non è più il percorso standard */}
        <Route
          path="/surfaces"
          element={
            <ProtectedRoute>
              <SurfaceChooser />
            </ProtectedRoute>
          }
        />

        {/* Layout shell persistente: tutte le superfici applicative */}
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/*"
            element={
              <ProtectedRoute roles={['produzione']}>
                <ProduzioneHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/logistica/*"
            element={
              <ProtectedRoute roles={['logistica']}>
                <LogisticaHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/magazzino/*"
            element={
              <ProtectedRoute roles={['magazzino']}>
                <MagazzinoHome />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Root: redirect in base alle superfici disponibili */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomeRedirect />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
