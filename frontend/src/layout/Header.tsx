import { useAuth } from '@/shared/hooks/useAuth'

export function Header() {
  const { logout, user } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="text-sm text-gray-500">
        {user ? <span>Usuario: {user.id}</span> : null}
      </div>

      <button
        onClick={logout}
        className="rounded-md px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
      >
        Cerrar sesión
      </button>
    </header>
  )
}
