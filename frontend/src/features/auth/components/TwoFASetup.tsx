import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import QRCode from 'qrcode'
import { useEnroll2FAMutation, useVerify2FAMutation } from '@/features/auth/hooks/useAuthMutations'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'

const verifySchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d+$/, 'El código debe ser numérico'),
})

type VerifyFormData = z.infer<typeof verifySchema>

export function TwoFASetup() {
  const enrollMutation = useEnroll2FAMutation()
  const verifyMutation = useVerify2FAMutation()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VerifyFormData>({
    resolver: zodResolver(verifySchema),
  })

  useEffect(() => {
    if (!enrollMutation.data) {
      enrollMutation.mutate()
    }
  }, [])

  useEffect(() => {
    if (enrollMutation.data?.uri) {
      const canvas = document.getElementById('qr-canvas') as HTMLCanvasElement
      if (canvas) {
        QRCode.toCanvas(canvas, enrollMutation.data.uri, { width: 200 })
      }
    }
  }, [enrollMutation.data?.uri])

  const onSubmit = (data: VerifyFormData) => {
    verifyMutation.mutate({ code: data.code })
  }

  if (enrollMutation.isPending) {
    return <LoadingSpinner size="lg" className="py-8" />
  }

  if (enrollMutation.isError) {
    return (
      <ErrorMessage message="Error al generar el código QR. Intentá de nuevo." />
    )
  }

  if (verifyMutation.isSuccess) {
    return (
      <div className="rounded-md bg-green-50 p-4 text-sm text-green-700">
        2FA activado correctamente.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-sm text-gray-600">
        Escaneá el código QR con tu app de autenticación (Google Authenticator,
        Authy, etc.)
      </div>

      <div className="flex justify-center">
        <canvas id="qr-canvas" />
      </div>

      {enrollMutation.data?.secret && (
        <div className="text-center text-xs text-gray-500">
          Código secreto: {enrollMutation.data.secret}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700">
            Verificá el código
          </label>
          <input
            id="code"
            type="text"
            inputMode="numeric"
            maxLength={6}
            placeholder="000000"
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-center text-lg tracking-widest shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            {...register('code')}
          />
          {errors.code && (
            <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
          )}
        </div>

        {verifyMutation.isError && (
          <ErrorMessage
            message={verifyMutation.error?.message || 'Código inválido'}
          />
        )}

        <button
          type="submit"
          disabled={verifyMutation.isPending}
          className="flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {verifyMutation.isPending ? <LoadingSpinner size="sm" /> : 'Verificar'}
        </button>
      </form>
    </div>
  )
}
