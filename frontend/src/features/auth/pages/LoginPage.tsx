import { Link } from 'react-router-dom'
import { LoginForm } from '@/features/auth/components/LoginForm'

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-6 rounded-lg bg-white p-8 shadow-md">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">activia-trace</h1>
          <p className="mt-1 text-sm text-gray-500">Iniciá sesión para continuar</p>
        </div>

        <LoginForm />

        <div className="text-center text-sm">
          <Link
            to="/forgot"
            className="text-blue-600 hover:text-blue-500"
          >
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
      </div>
    </div>
  )
}
