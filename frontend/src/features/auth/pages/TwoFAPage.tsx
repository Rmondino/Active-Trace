import { TwoFAForm } from '@/features/auth/components/TwoFAForm'

export function TwoFAPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-6 rounded-lg bg-white p-8 shadow-md">
        <div className="text-center">
          <h1 className="text-xl font-bold text-gray-900">
            Autenticación en dos pasos
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Ingresá el código de 6 dígitos de tu app de autenticación
          </p>
        </div>

        <TwoFAForm />
      </div>
    </div>
  )
}
