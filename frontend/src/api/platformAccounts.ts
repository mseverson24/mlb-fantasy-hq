import { apiClient } from './client'
import type { League, PlatformAccount } from '../types/api'

export async function listPlatformAccounts(): Promise<PlatformAccount[]> {
  const { data } = await apiClient.get<PlatformAccount[]>('/platform-accounts')
  return data
}

export async function deletePlatformAccount(id: string): Promise<void> {
  await apiClient.delete(`/platform-accounts/${id}`)
}

export interface CBSCookiePayload {
  leagueName: string
  authSession: string
  authState?: string
  awsAlb?: string
  awsAlbCors?: string
}

export async function linkCBSAccount(payload: CBSCookiePayload): Promise<League> {
  const { data } = await apiClient.post<League>('/platform-accounts/cbs', {
    league_name: payload.leagueName,
    auth_session: payload.authSession,
    auth_state: payload.authState || undefined,
    aws_alb: payload.awsAlb || undefined,
    aws_alb_cors: payload.awsAlbCors || undefined,
  })
  return data
}

export interface RawDebugResult {
  page: string
  status: string
  html_snippet: string | null
  total_length: number | null
  offset: number
  error: string | null
  status_code: number | null
  final_url: string | null
  redirect_chain: string[]
  set_cookie_names: string[]
}

export async function getCBSRawDebug(page: string, offset = 0): Promise<RawDebugResult> {
  const { data } = await apiClient.get<RawDebugResult>('/platform-accounts/cbs/raw-debug', {
    params: { page, offset },
  })
  return data
}
