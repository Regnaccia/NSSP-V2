import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import Login from '@/pages/Login'
import SurfaceChooser from '@/pages/SurfaceChooser'
import AdminHome from '@/pages/surfaces/AdminHome'
import LogisticaHome from '@/pages/surfaces/LogisticaHome'
import MagazzinoHome from '@/pages/surfaces/MagazzinoHome'
import ProduzioneHome from '@/pages/surfaces/ProduzioneHome'

/**
 * Redirect iniziale dopo login.
 *
 * - 1 superficie disponibile → redirect diretto (DL-ARCH-V2-004 §7)
 * - più superfici → pagina di scelta
 */
function HomeRedirect() {
  const surfaces = useAuthStore((s) => s.available_surfaces)

  if (surfaces.length === 0) {
    return <Navigate to="/login" replace />
  }
  if (surfaces.length === 1) {
    return <Navigate to={surfaces[0].path} replace />
  }
  return <Navigate to="/surfaces" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Pubblica */}
        <Route path="/login" element={<Login />} />

        {/* Scelta superficie (utenti multi-ruolo) */}
        <Route
          path="/surfaces"
          element={
            <ProtectedRoute>
              <SurfaceChooser />
            </ProtectedRoute>
          }
        />

        {/* Superfici applicative */}
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
