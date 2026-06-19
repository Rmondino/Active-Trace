import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'

const cards = [
  { label: 'Mis Comisiones', path: '/comision', icon: '📚', roles: ['ADMIN', 'PROFESOR', 'TUTOR', 'COORDINADOR'] },
  { label: 'Mi Perfil', path: '/perfil', icon: '👤', roles: [] },
  { label: 'Mensajes', path: '/inbox', icon: '✉️', roles: [] },
  { label: 'Carreras', path: '/admin/carreras', icon: '🎓', roles: ['ADMIN'] },
  { label: 'Cohortes', path: '/admin/cohortes', icon: '📅', roles: ['ADMIN'] },
  { label: 'Materias', path: '/admin/materias', icon: '📖', roles: ['ADMIN'] },
  { label: 'Usuarios', path: '/admin/usuarios', icon: '👥', roles: ['ADMIN'] },
  { label: 'Auditoría', path: '/admin/auditoria', icon: '📋', roles: ['ADMIN'] },
  { label: 'Liquidaciones', path: '/liquidaciones', icon: '💰', roles: ['FINANZAS', 'ADMIN'] },
  { label: 'Grilla Salarial', path: '/liquidaciones/grilla', icon: '📊', roles: ['FINANZAS', 'ADMIN'] },
  { label: 'Facturas', path: '/facturas', icon: '🧾', roles: ['FINANZAS', 'ADMIN'] },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userRoles: string[] = user?.roles ?? []

  const visible = cards.filter(c => !c.roles.length || c.roles.some(r => userRoles.includes(r)))

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">Panel Principal</h1>
      <p className="text-gray-600 mb-6">
        Bienvenido, {user?.nombre ?? 'usuario'} — Roles: {userRoles.join(', ') || 'Ninguno'}
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map(c => (
          <button
            key={c.path}
            onClick={() => navigate(c.path)}
            className="bg-white p-6 rounded-xl shadow hover:shadow-md transition text-left flex items-center gap-4"
          >
            <span className="text-3xl">{c.icon}</span>
            <span className="font-medium text-gray-800">{c.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
