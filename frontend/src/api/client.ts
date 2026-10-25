import axios, { type InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001/api/v1'
const REQUEST_TIMEOUT_MS = 60_000

export const apiClient = axios.create({ baseURL: API_BASE_URL, timeout: REQUEST_TIMEOUT_MS })

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('mlbhq_access_token')
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refreshToken = localStorage.getItem('mlbhq_refresh_token')
  if (!refreshToken) throw new Error('No refresh token available')
  const response = await axios.post(
    `${API_BASE_URL}/auth/refresh`,
    { refresh_token: refreshToken },
    { timeout: REQUEST_TIMEOUT_MS },
  )
  const { access_token, refresh_token } = response.data
  localStorage.setItem('mlbhq_access_token', access_token)
  localStorage.setItem('mlbhq_refresh_token', refresh_token)
  return access_token
}

const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh']

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryableConfig | undefined
    const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => originalRequest?.url?.includes(path))
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      try {
        refreshPromise ??= refreshAccessToken()
        const newToken = await refreshPromise
        refreshPromise = null
        originalRequest.headers.set('Authorization', `Bearer ${newToken}`)
        return apiClient(originalRequest)
      } catch (refreshError) {
        refreshPromise = null
        localStorage.removeItem('mlbhq_access_token')
        localStorage.removeItem('mlbhq_refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)
