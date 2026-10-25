import { apiClient } from './client'
import type { League, PlatformAccount } from '../types/api'

export async function listPlatformAccounts(): Promise<PlatformAccount[]> {
  const { data } = await apiClient.get<PlatformAccount[]>('/platform-accounts')
  return data
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
