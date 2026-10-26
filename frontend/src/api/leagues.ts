import { apiClient } from './client'
import type { League, RosterPlayer, StandingsRow, SuggestionsResponse } from '../types/api'

export async function listLeagues(): Promise<League[]> {
  const { data } = await apiClient.get<League[]>('/leagues')
  return data
}

export async function syncLeague(leagueId: string): Promise<League> {
  const { data } = await apiClient.post<League>(`/leagues/${leagueId}/sync`)
  return data
}

export async function getMyRoster(leagueId: string): Promise<RosterPlayer[]> {
  const { data } = await apiClient.get<RosterPlayer[]>(`/leagues/${leagueId}/roster`)
  return data
}

export async function getStandings(leagueId: string): Promise<StandingsRow[]> {
  const { data } = await apiClient.get<StandingsRow[]>(`/leagues/${leagueId}/standings`)
  return data
}

export async function getSuggestions(leagueId: string): Promise<SuggestionsResponse> {
  const { data } = await apiClient.get<SuggestionsResponse>(`/leagues/${leagueId}/suggestions`)
  return data
}
