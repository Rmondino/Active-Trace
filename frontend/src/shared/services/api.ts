import axios from 'axios'

let accessToken: string | null = null
let refreshToken: string | null = null
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}> = []

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/api/auth/refresh'
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post(
          `${api.defaults.baseURL}/api/auth/refresh`,
          { refresh_token: refreshToken },
        )
        const { access_token: newAccess, refresh_token: newRefresh } = response.data
        setTokens(newAccess, newRefresh)

        processQueue(null, newAccess)

        originalRequest.headers.Authorization = `Bearer ${newAccess}`
        return api(originalRequest)
      } catch (err) {
        processQueue(err, null)
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

export function setTokens(access: string | null, refresh: string | null) {
  accessToken = access
  refreshToken = refresh
  if (access) {
    localStorage.setItem('access_token', access)
  } else {
    localStorage.removeItem('access_token')
  }
  if (refresh) {
    localStorage.setItem('refresh_token', refresh)
  } else {
    localStorage.removeItem('refresh_token')
  }
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function getAccessToken() {
  return accessToken
}

const storedAccess = localStorage.getItem('access_token')
const storedRefresh = localStorage.getItem('refresh_token')
if (storedAccess) accessToken = storedAccess
if (storedRefresh) refreshToken = storedRefresh

export default api
