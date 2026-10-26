import { apiClient } from './client'
import type { PlatformAccount } from '../types/api'

export async function listPlatformAccounts(): Promise<PlatformAccount[]> {
  const { data } = await apiClient.get<PlatformAccount[]>('/platform-accounts')
  return data
}

export async function deletePlatformAccount(id: string): Promise<void> {
  await apiClient.delete(`/platform-accounts/${id}`)
}

export interface ConnectCBSResult {
  leagueName: string
  ingestToken: string
}

export async function connectCBSAccount(leagueName: string): Promise<ConnectCBSResult> {
  const { data } = await apiClient.post('/platform-accounts/cbs', { league_name: leagueName })
  return { leagueName: data.league_name, ingestToken: data.ingest_token }
}

export interface RawDebugResult {
  page: string
  status: string
  html_snippet: string | null
  total_length: number | null
  offset: number
  error: string | null
  ingested_at: string | null
}

export async function getCBSRawDebug(page: string, offset = 0, find?: string): Promise<RawDebugResult> {
  const { data } = await apiClient.get<RawDebugResult>('/platform-accounts/cbs/raw-debug', {
    params: { page, offset, find: find || undefined },
  })
  return data
}
