import { apiClient } from './client'
import type { User } from '../types/api'

interface TokenResponse {
  access_token: string
  refresh_token: string
}

function storeTokens(tokens: TokenResponse): void {
  localStorage.setItem('mlbhq_access_token', tokens.access_token)
  localStorage.setItem('mlbhq_refresh_token', tokens.refresh_token)
}

export async function register(email: string, password: string, displayName: string): Promise<void> {
  const { data } = await apiClient.post<TokenResponse>('/auth/register', {
    email,
    password,
    display_name: displayName,
  })
  storeTokens(data)
}

export async function login(email: string, password: string): Promise<void> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  storeTokens(data)
}

export function logout(): void {
  localStorage.removeItem('mlbhq_access_token')
  localStorage.removeItem('mlbhq_refresh_token')
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me')
  return data
}
