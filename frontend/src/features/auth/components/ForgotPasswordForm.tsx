import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useForgotMutation } from '@/features/auth/hooks/useAuthMutations'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'

const forgotSchema = z.object({
  email: z.string().email('Email inválido'),
})

type ForgotFormData = z.infer<typeof forgotSchema>

export function ForgotPasswordForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  })

  const forgotMutation = useForgotMutation()

  const onSubmit = (data: ForgotFormData) => {
    forgotMutation.mutate(data)
  }

  if (forgotMutation.isSuccess) {
    return (
      <div className="rounded-md bg-green-50 p-4 text-sm text-green-700">
        Si el email está registrado, vas a recibir instrucciones para recuperar tu
        contraseña.
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          {...register('email')}
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      {forgotMutation.isError && (
        <ErrorMessage
          message={forgotMutation.error?.message || 'Error al procesar la solicitud'}
        />
      )}

      <button
        type="submit"
        disabled={forgotMutation.isPending}
        className="flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {forgotMutation.isPending ? (
          <LoadingSpinner size="sm" />
        ) : (
          'Enviar instrucciones'
        )}
      </button>
    </form>
  )
}
