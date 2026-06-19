import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authService } from '@/features/auth/services/authService'
import { useAuth } from '@/shared/hooks/useAuth'

export function useLoginMutation() {
  const navigate = useNavigate()
  const { login } = useAuth()

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: (data) => {
      if (data.requires_2fa && data.session_token) {
        navigate('/login/2fa', { state: { sessionToken: data.session_token } })
      } else if (data.access_token && data.refresh_token && data.user) {
        login(data.access_token, data.refresh_token, data.user)
        navigate('/', { replace: true })
      }
    },
  })
}

export function useTwoFAMutation() {
  const navigate = useNavigate()
  const { login } = useAuth()

  return useMutation({
    mutationFn: ({
      sessionToken,
      code,
    }: {
      sessionToken: string
      code: string
    }) => authService.authenticate2fa(sessionToken, code),
    onSuccess: (data) => {
      login(data.access_token, data.refresh_token, data.user)
      navigate('/', { replace: true })
    },
  })
}

export function useForgotMutation() {
  return useMutation({
    mutationFn: ({ email }: { email: string }) => authService.forgot(email),
  })
}

export function useResetMutation() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: ({
      token,
      newPassword,
    }: {
      token: string
      newPassword: string
    }) => authService.reset(token, newPassword),
    onSuccess: () => {
      navigate('/login', { replace: true })
    },
  })
}

export function useEnroll2FAMutation() {
  return useMutation({
    mutationFn: () => authService.enroll2fa(),
  })
}

export function useVerify2FAMutation() {
  return useMutation({
    mutationFn: ({ code }: { code: string }) => authService.verify2fa(code),
  })
}
