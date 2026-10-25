import { apiClient } from './client'
import type { RankedPlayer } from '../types/api'

export async function getRankings(): Promise<RankedPlayer[]> {
  const { data } = await apiClient.get<RankedPlayer[]>('/rankings')
  return data
}
