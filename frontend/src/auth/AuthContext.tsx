import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import type { User } from '../types/api'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('mlbhq_access_token')
    if (!token) {
      setIsLoading(false)
      return
    }
    authApi
      .getMe()
      .then(setUser)
      .catch(() => authApi.logout())
      .finally(() => setIsLoading(false))
  }, [])

  async function login(email: string, password: string) {
    await authApi.login(email, password)
    setUser(await authApi.getMe())
  }

  async function register(email: string, password: string, displayName: string) {
    await authApi.register(email, password, displayName)
    setUser(await authApi.getMe())
  }

  function logout() {
    authApi.logout()
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
