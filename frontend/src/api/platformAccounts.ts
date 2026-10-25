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
