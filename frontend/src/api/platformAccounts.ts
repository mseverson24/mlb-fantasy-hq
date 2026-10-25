import { apiClient } from './client'
import type { League, PlatformAccount } from '../types/api'

export async function listPlatformAccounts(): Promise<PlatformAccount[]> {
  const { data } = await apiClient.get<PlatformAccount[]>('/platform-accounts')
  return data
}

export async function linkCBSAccount(username: string, password: string, leagueName: string): Promise<League> {
  const { data } = await apiClient.post<League>('/platform-accounts/cbs', {
    username,
    password,
    league_name: leagueName,
  })
  return data
}

export interface LoginDebugResult {
  status_code: number
  final_url: string
  token_found: boolean
  cookie_names: string[]
  response_length: number
  html_snippet: string
}

export async function debugCBSLogin(username: string, password: string, leagueName: string): Promise<LoginDebugResult> {
  const { data } = await apiClient.post<LoginDebugResult>('/platform-accounts/cbs/debug-login', {
    username,
    password,
    league_name: leagueName,
  })
  return data
}
