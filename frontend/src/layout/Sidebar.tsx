import { Link, useLocation } from 'react-router-dom'
import { useState, useMemo } from 'react'
import { useAuth } from '@/shared/hooks/useAuth'

interface NavItem {
  label: string
  path: string
  roles?: string[]
}

interface NavGroup {
  label: string
  items: NavItem[]
  roles?: string[]
}

const navGroups: NavGroup[] = [
  {
    label: 'GENERAL',
    items: [
      { label: 'Dashboard', path: '/' },
      { label: 'Mi Perfil', path: '/perfil' },
      { label: 'Mensajes', path: '/inbox' },
      { label: 'Configurar 2FA', path: '/2fa/setup' },
    ],
  },
  {
    label: 'COMISIONES',
    items: [
      { label: 'Mis Comisiones', path: '/comision' },
    ],
  },
  {
    label: 'FINANZAS',
    roles: ['FINANZAS', 'ADMIN'],
    items: [
      { label: 'Grilla Salarial', path: '/liquidaciones/grilla' },
      { label: 'Liquidaciones', path: '/liquidaciones' },
      { label: 'KPIs Contables', path: '/liquidaciones/kpis' },
      { label: 'Facturas', path: '/facturas' },
    ],
  },
  {
    label: 'ADMIN',
    roles: ['ADMIN'],
    items: [
      { label: 'Carreras', path: '/admin/carreras' },
      { label: 'Cohortes', path: '/admin/cohortes' },
      { label: 'Materias', path: '/admin/materias' },
      { label: 'Usuarios', path: '/admin/usuarios' },
      { label: 'Auditoría', path: '/admin/auditoria' },
    ],
  },
]

export function Sidebar() {
  const location = useLocation()
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const { user } = useAuth()

  const userRoles = useMemo(() => {
    if (!user?.roles) return []
    return user.roles.map((r: string) => r.toUpperCase())
  }, [user])

  const visibleGroups = useMemo(() => {
    return navGroups.filter(g => {
      if (!g.roles) return true
      return g.roles.some(r => userRoles.includes(r))
    })
  }, [userRoles])

  const toggleGroup = (label: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }

  const isGroupActive = (items: { path: string }[]) =>
    items.some(item => location.pathname === item.path || location.pathname.startsWith(item.path + '/'))

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center border-b border-gray-200 px-6">
        <span className="text-lg font-bold text-gray-900">activia-trace</span>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {visibleGroups.map((group) => {
          const groupActive = isGroupActive(group.items)
          const collapsed = collapsedGroups.has(group.label)

          return (
            <div key={group.label} className="mb-2">
              <button
                onClick={() => toggleGroup(group.label)}
                className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wider ${
                  groupActive ? 'text-blue-700' : 'text-gray-500'
                }`}
              >
                <span>{group.label}</span>
                <svg className={`h-3 w-3 transition-transform ${collapsed ? '' : 'rotate-90'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              {!collapsed && (
                <div className="mt-1 space-y-1">
                  {group.items.map((item) => {
                    const isActive = location.pathname === item.path
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        className={`block rounded-md px-3 py-2 text-sm font-medium ${
                          isActive
                            ? 'bg-blue-50 text-blue-700'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        {item.label}
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
