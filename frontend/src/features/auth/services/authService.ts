import api from '@/shared/services/api'
import type {
  LoginResponse,
  RefreshResponse,
  Authenticate2FAResponse,
  ForgotResponse,
  ResetResponse,
  EnrollResponse,
} from '@/shared/types/auth'

export const authService = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/api/auth/login', { email, password }).then((r) => r.data),

  refresh: (refreshToken: string) =>
    api.post<RefreshResponse>('/api/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data),

  logout: (refreshToken: string) =>
    api.post('/api/auth/logout', { refresh_token: refreshToken }),

  forgot: (email: string) =>
    api.post<ForgotResponse>('/api/auth/forgot', { email }).then((r) => r.data),

  reset: (token: string, newPassword: string) =>
    api.post<ResetResponse>('/api/auth/reset', { token, new_password: newPassword }).then((r) => r.data),

  authenticate2fa: (sessionToken: string, code: string) =>
    api
      .post<Authenticate2FAResponse>('/api/auth/2fa/authenticate', {
        session_token: sessionToken,
        code,
      })
      .then((r) => r.data),

  enroll2fa: () =>
    api.post<EnrollResponse>('/api/auth/2fa/enroll').then((r) => r.data),

  verify2fa: (code: string) =>
    api.post('/api/auth/2fa/verify', { code }),
}
