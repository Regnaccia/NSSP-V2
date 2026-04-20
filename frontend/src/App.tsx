import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/app/authStore'
import { apiClient } from '@/api/client'
import type { Surface } from '@/types/api'
import AppShell from '@/components/AppShell'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import Login from '@/pages/Login'
import SurfaceChooser from '@/pages/SurfaceChooser'
import AdminHome from '@/pages/surfaces/AdminHome'
import AdminStockLogicPage from '@/pages/surfaces/AdminStockLogicPage'
import AdminProposalLogicPage from '@/pages/surfaces/AdminProposalLogicPage'
import AdminWarningsPage from '@/pages/surfaces/AdminWarningsPage'
import AdminLogicConfigPage from '@/pages/surfaces/AdminLogicConfigPage'
import PlanningWorkspacePage from '@/pages/surfaces/PlanningWorkspacePage'
import LogisticaHome from '@/pages/surfaces/LogisticaHome'
import MagazzinoHome from '@/pages/surfaces/MagazzinoHome'
import ProduzioneHome from '@/pages/surfaces/ProduzioneHome'
import FamigliePage from '@/pages/surfaces/FamigliePage'
import ProduzioniPage from '@/pages/surfaces/ProduzioniPage'
import CriticitaPage from '@/pages/surfaces/CriticitaPage'
import PlanningCandidatesPage from '@/pages/surfaces/PlanningCandidatesPage'
import ProductionProposalsPage from '@/pages/surfaces/ProductionProposalsPage'
import WarningsPage from '@/pages/surfaces/WarningsPage'

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

/**
 * Aggiorna le superfici disponibili chiamando /auth/me al boot dell'app.
 * Garantisce che le sessioni persistite in localStorage riflettano
 * la logica backend corrente (es. nuove surface cross-role come /warnings).
 */
function SessionRefresh() {
  const { isAuthenticated, updateSurfaces } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated) return
    apiClient
      .get<{ available_surfaces: Surface[] }>('/auth/me')
      .then((r) => updateSurfaces(r.data.available_surfaces))
      .catch(() => {
        // Sessione scaduta o errore di rete: non agisce, lascia la redirect di auth
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <SessionRefresh />
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
          {/* Admin — livello secondario: /admin/utenti (DL-UIX-V2-003) */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['admin']}>
                <Navigate to="/admin/utenti" replace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/utenti"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/stock-logic"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminStockLogicPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/proposal-logic"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminProposalLogicPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/warnings"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminWarningsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/logic-config"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminLogicConfigPage />
              </ProtectedRoute>
            }
          />

          {/* Logistica — livello secondario: /logistica/clienti-destinazioni (DL-UIX-V2-003) */}
          <Route
            path="/logistica"
            element={
              <ProtectedRoute roles={['logistica']}>
                <Navigate to="/logistica/clienti-destinazioni" replace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/logistica/clienti-destinazioni"
            element={
              <ProtectedRoute roles={['logistica']}>
                <LogisticaHome />
              </ProtectedRoute>
            }
          />

          {/* Produzione — livello secondario: /produzione/articoli (DL-UIX-V2-003) */}
          <Route
            path="/produzione"
            element={
              <ProtectedRoute roles={['produzione']}>
                <Navigate to="/produzione/articoli" replace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/articoli"
            element={
              <ProtectedRoute roles={['produzione']}>
                <ProduzioneHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/famiglie"
            element={
              <ProtectedRoute roles={['produzione']}>
                <FamigliePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/produzioni"
            element={
              <ProtectedRoute roles={['produzione']}>
                <ProduzioniPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/criticita"
            element={
              <ProtectedRoute roles={['produzione']}>
                <CriticitaPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/planning-candidates"
            element={
              <ProtectedRoute roles={['produzione']}>
                <PlanningCandidatesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/produzione/proposals"
            element={
              <ProtectedRoute roles={['produzione']}>
                <ProductionProposalsPage />
              </ProtectedRoute>
            }
          />
          {/* Planning Workspace — shadow view (TASK-V2-137) */}
          <Route
            path="/produzione/planning-workspace"
            element={
              <ProtectedRoute roles={['produzione']}>
                <PlanningWorkspacePage />
              </ProtectedRoute>
            }
          />
          {/* Warnings — surface root trasversale (TASK-V2-135) */}
          <Route
            path="/warnings"
            element={
              <ProtectedRoute roles={['admin', 'produzione', 'magazzino', 'logistica']}>
                <WarningsPage />
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
