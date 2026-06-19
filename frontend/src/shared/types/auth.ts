export interface User {
  id: string
}

export interface LoginResponse {
  access_token: string | null
  refresh_token: string | null
  token_type: string | null
  requires_2fa: boolean | null
  session_token: string | null
  user: User | null
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Authenticate2FAResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface ForgotResponse {
  message: string
  token?: string
}

export interface ResetResponse {
  message: string
}

export interface EnrollResponse {
  secret: string
  uri: string
}

export interface AuthState {
  isAuthenticated: boolean
  user: User | null
  accessToken: string | null
  refreshToken: string | null
}
