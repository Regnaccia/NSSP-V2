import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/api/client'
import type { Surface } from '@/types/api'

// ─── Tipi ────────────────────────────────────────────────────────────────────

interface UserItem {
  id: number
  username: string
  attivo: boolean
  roles: string[]
  available_surfaces: Surface[]
}

const ALL_ROLES = ['admin', 'produzione', 'logistica', 'magazzino']

// ─── Componente modale generico ───────────────────────────────────────────────

function Modal({ title, onClose, children }: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-background border rounded-xl shadow-lg w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg">{title}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

// ─── Modale crea utente ───────────────────────────────────────────────────────

function CreateUserModal({ onClose, onCreated }: {
  onClose: () => void
  onCreated: (user: UserItem) => void
}) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const toggleRole = (role: string) =>
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role]
    )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) return
    setLoading(true)
    try {
      const { data } = await apiClient.post<UserItem>('/admin/users', {
        username,
        password,
        roles: selectedRoles,
      })
      onCreated(data)
      toast.success(`Utente "${data.username}" creato`)
      onClose()
    } catch (err: unknown) {
      const msg = extractError(err, 'Errore nella creazione utente')
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Nuovo utente" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Username">
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoFocus
            className={inputCls}
            disabled={loading}
          />
        </Field>
        <Field label="Password iniziale">
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className={inputCls}
            disabled={loading}
          />
        </Field>
        <Field label="Ruoli">
          <div className="flex flex-wrap gap-2">
            {ALL_ROLES.map(role => (
              <label key={role} className="flex items-center gap-1 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedRoles.includes(role)}
                  onChange={() => toggleRole(role)}
                  disabled={loading}
                />
                {role}
              </label>
            ))}
          </div>
        </Field>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className={btnSecondary} disabled={loading}>Annulla</button>
          <button type="submit" className={btnPrimary} disabled={loading || !username || !password}>
            {loading ? 'Creando...' : 'Crea utente'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Modale gestione ruoli ────────────────────────────────────────────────────

function EditRolesModal({ user, onClose, onUpdated }: {
  user: UserItem
  onClose: () => void
  onUpdated: (user: UserItem) => void
}) {
  const [selectedRoles, setSelectedRoles] = useState<string[]>(user.roles)
  const [loading, setLoading] = useState(false)

  const toggleRole = (role: string) =>
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role]
    )

  const handleSave = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.put<UserItem>(`/admin/users/${user.id}/roles`, {
        roles: selectedRoles,
      })
      onUpdated(data)
      toast.success(`Ruoli di "${data.username}" aggiornati`)
      onClose()
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nella modifica ruoli'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={`Ruoli — ${user.username}`} onClose={onClose}>
      <div className="space-y-4">
        <div className="flex flex-wrap gap-3">
          {ALL_ROLES.map(role => (
            <label key={role} className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={selectedRoles.includes(role)}
                onChange={() => toggleRole(role)}
                disabled={loading}
              />
              {role}
            </label>
          ))}
        </div>
        {selectedRoles.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Superfici risultanti:</p>
            <div className="flex flex-wrap gap-1">
              {derivePreviewSurfaces(selectedRoles).map(s => (
                <span key={s.role} className="text-xs bg-muted px-2 py-0.5 rounded">{s.label}</span>
              ))}
            </div>
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className={btnSecondary} disabled={loading}>Annulla</button>
          <button onClick={handleSave} className={btnPrimary} disabled={loading}>
            {loading ? 'Salvando...' : 'Salva'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Surface Admin principale ─────────────────────────────────────────────────

export default function AdminHome() {
  const [users, setUsers] = useState<UserItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editRolesUser, setEditRolesUser] = useState<UserItem | null>(null)

  useEffect(() => {
    apiClient.get<UserItem[]>('/admin/users')
      .then(r => setUsers(r.data))
      .catch(() => toast.error('Impossibile caricare gli utenti'))
      .finally(() => setLoading(false))
  }, [])

  const updateUser = (updated: UserItem) =>
    setUsers(prev => prev.map(u => u.id === updated.id ? updated : u))

  const handleToggleActive = async (user: UserItem) => {
    try {
      const { data } = await apiClient.patch<UserItem>(
        `/admin/users/${user.id}/active`,
        { attivo: !user.attivo }
      )
      updateUser(data)
      toast.success(`${data.username} ${data.attivo ? 'attivato' : 'disattivato'}`)
    } catch (err: unknown) {
      toast.error(extractError(err, 'Errore nel cambio stato'))
    }
  }

  return (
    <div>
      <main className="p-6 max-w-5xl mx-auto space-y-4">
        {/* Titolo sezione + azione */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Utenti</h1>
          <button onClick={() => setShowCreate(true)} className={btnPrimary}>
            + Nuovo utente
          </button>
        </div>

        {/* Tabella utenti */}
        {loading ? (
          <p className="text-sm text-muted-foreground">Caricamento...</p>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Username</th>
                  <th className="text-left px-4 py-2 font-medium">Ruoli</th>
                  <th className="text-left px-4 py-2 font-medium">Superfici</th>
                  <th className="text-left px-4 py-2 font-medium">Stato</th>
                  <th className="text-left px-4 py-2 font-medium">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id} className="border-t hover:bg-muted/20">
                    <td className="px-4 py-3 font-medium">{user.username}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {user.roles.length > 0
                          ? user.roles.map(r => (
                              <span key={r} className="text-xs bg-secondary px-2 py-0.5 rounded">{r}</span>
                            ))
                          : <span className="text-xs text-muted-foreground">nessuno</span>
                        }
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {user.available_surfaces.length > 0
                          ? user.available_surfaces.map(s => (
                              <span key={s.role} className="text-xs bg-muted px-2 py-0.5 rounded">{s.label}</span>
                            ))
                          : <span className="text-xs text-muted-foreground">—</span>
                        }
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${user.attivo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {user.attivo ? 'Attivo' : 'Inattivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => setEditRolesUser(user)}
                          className={btnSecondary + ' text-xs py-1 px-2'}
                        >
                          Ruoli
                        </button>
                        <button
                          onClick={() => handleToggleActive(user)}
                          className={btnSecondary + ' text-xs py-1 px-2'}
                        >
                          {user.attivo ? 'Disattiva' : 'Attiva'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">
                      Nessun utente
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Modali */}
      {showCreate && (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={u => setUsers(prev => [...prev, u])}
        />
      )}
      {editRolesUser && (
        <EditRolesModal
          user={editRolesUser}
          onClose={() => setEditRolesUser(null)}
          onUpdated={u => { updateUser(u); setEditRolesUser(null) }}
        />
      )}
    </div>
  )
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const inputCls = 'w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50'
const btnPrimary = 'py-2 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity'
const btnSecondary = 'py-2 px-4 border rounded-md text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  )
}

const SURFACE_MAP: Record<string, { path: string; label: string }> = {
  admin: { path: '/admin', label: 'Admin' },
  produzione: { path: '/produzione', label: 'Produzione' },
  logistica: { path: '/logistica', label: 'Logistica' },
  magazzino: { path: '/magazzino', label: 'Magazzino' },
}

function derivePreviewSurfaces(roles: string[]): Surface[] {
  return roles
    .filter(r => r in SURFACE_MAP)
    .map(r => ({ role: r, ...SURFACE_MAP[r] }))
}

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return resp.data.detail
  }
  return fallback
}
