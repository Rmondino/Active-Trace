import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useState,
  type Dispatch,
  type ReactNode,
} from 'react'
import type { User, AuthState } from '@/shared/types/auth'
import { setTokens as apiSetTokens, clearTokens as apiClearTokens } from '@/shared/services/api'

type AuthAction =
  | { type: 'LOGIN'; payload: { accessToken: string; refreshToken: string; user: User } }
  | { type: 'LOGOUT' }
  | { type: 'SET_TOKENS'; payload: { accessToken: string; refreshToken: string } }

interface AuthContextValue {
  isAuthenticated: boolean
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  setTokens: (access: string, refresh: string) => void
}

function loadUser(): User | null {
  try {
    const raw = localStorage.getItem('auth_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  refreshToken: null,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN':
      localStorage.setItem('auth_user', JSON.stringify(action.payload.user))
      return {
        isAuthenticated: true,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
      }
    case 'LOGOUT':
      localStorage.removeItem('auth_user')
      return { isAuthenticated: false, user: null, accessToken: null, refreshToken: null }
    case 'SET_TOKENS':
      return {
        ...state,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
      }
  }
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [state, dispatch]: [AuthState, Dispatch<AuthAction>] = useReducer(
    authReducer,
    initialState,
    () => {
      const accessToken = localStorage.getItem('access_token')
      const refreshToken = localStorage.getItem('refresh_token')
      const user = loadUser()
      if (accessToken && refreshToken && user) {
        return {
          isAuthenticated: true,
          user,
          accessToken,
          refreshToken,
        }
      }
      return initialState
    },
  )

  useEffect(() => {
    setLoading(false)
  }, [])

  useEffect(() => {
    if (state.accessToken && state.refreshToken) {
      apiSetTokens(state.accessToken, state.refreshToken)
    }
  }, [state.accessToken, state.refreshToken])

  const login = (accessToken: string, refreshToken: string, user: User) => {
    apiSetTokens(accessToken, refreshToken)
    dispatch({ type: 'LOGIN', payload: { accessToken, refreshToken, user } })
  }

  const logout = () => {
    apiClearTokens()
    dispatch({ type: 'LOGOUT' })
  }

  const setTokens = (access: string, refresh: string) => {
    apiSetTokens(access, refresh)
    dispatch({ type: 'SET_TOKENS', payload: { accessToken: access, refreshToken: refresh } })
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        loading,
        login,
        logout,
        setTokens,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
