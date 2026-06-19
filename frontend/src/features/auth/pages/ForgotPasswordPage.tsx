import { Link } from 'react-router-dom'
import { ForgotPasswordForm } from '@/features/auth/components/ForgotPasswordForm'

export function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-6 rounded-lg bg-white p-8 shadow-md">
        <div className="text-center">
          <h1 className="text-xl font-bold text-gray-900">
            Recuperar contraseña
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Te enviaremos un link para restablecerla
          </p>
        </div>

        <ForgotPasswordForm />

        <div className="text-center text-sm">
          <Link
            to="/login"
            className="text-blue-600 hover:text-blue-500"
          >
            Volver a inicio de sesión
          </Link>
        </div>
      </div>
    </div>
  )
}
