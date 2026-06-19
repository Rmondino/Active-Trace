import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useLocation } from 'react-router-dom'
import { useTwoFAMutation } from '@/features/auth/hooks/useAuthMutations'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'

const twoFASchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d+$/, 'El código debe ser numérico'),
})

type TwoFAFormData = z.infer<typeof twoFASchema>

export function TwoFAForm() {
  const location = useLocation()
  const sessionToken = (location.state as { sessionToken?: string } | null)
    ?.sessionToken

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFAFormData>({
    resolver: zodResolver(twoFASchema),
  })

  const twoFAMutation = useTwoFAMutation()

  const onSubmit = (data: TwoFAFormData) => {
    if (!sessionToken) return
    twoFAMutation.mutate({ sessionToken, code: data.code })
  }

  if (!sessionToken) {
    return (
      <ErrorMessage message="Sesión no válida. Por favor, iniciá sesión nuevamente." />
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="code" className="block text-sm font-medium text-gray-700">
          Código de verificación
        </label>
        <input
          id="code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="000000"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-center text-lg tracking-widest shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          {...register('code')}
        />
        {errors.code && (
          <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
        )}
      </div>

      {twoFAMutation.isError && (
        <ErrorMessage
          message={twoFAMutation.error?.message || 'Código inválido'}
        />
      )}

      <button
        type="submit"
        disabled={twoFAMutation.isPending}
        className="flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {twoFAMutation.isPending ? (
          <LoadingSpinner size="sm" />
        ) : (
          'Verificar'
        )}
      </button>
    </form>
  )
}
