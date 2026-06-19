import { Outlet, NavLink, useParams } from 'react-router-dom'

const tabs = [
  { label: 'Calificaciones', path: 'calificaciones' },
  { label: 'Atrasados', path: 'atrasados' },
  { label: 'Comunicación', path: 'comunicacion' },
]

export function ComisionLayout() {
  const { materiaId, cohorteId } = useParams<{ materiaId: string; cohorteId: string }>()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Comisión</h1>
        <p className="text-sm text-gray-500 mt-1">Materia: {materiaId} — Cohorte: {cohorteId}</p>
      </div>

      <nav className="flex border-b border-gray-200">
        {tabs.map(tab => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              `px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  )
}
