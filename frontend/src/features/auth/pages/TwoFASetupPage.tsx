import { TwoFASetup } from '@/features/auth/components/TwoFASetup'

export function TwoFASetupPage() {
  return (
    <div className="mx-auto max-w-md space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Configurar 2FA
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Vinculá tu cuenta con una app de autenticación
        </p>
      </div>

      <TwoFASetup />
    </div>
  )
}
