export interface User {
  id: string
  email: string
  display_name: string
  is_admin: boolean
}

export interface PlatformAccount {
  id: string
  platform: string
  display_name: string | null
  is_connected: boolean
}

export interface League {
  id: string
  name: string
  season: string
  scoring_type: string | null
  num_teams: number | null
  roster_positions: string[]
  last_synced_at: string | null
}

export interface PlayerStat {
  season: string
  games: number | null
  at_bats: number | null
  hits: number | null
  runs: number | null
  home_runs: number | null
  rbi: number | null
  stolen_bases: number | null
  batting_avg: number | null
  ops: number | null
  wins: number | null
  losses: number | null
  saves: number | null
  innings_pitched: number | null
  strikeouts: number | null
  era: number | null
  whip: number | null
}

export interface RosterPlayer {
  player_id: string
  full_name: string
  position: string | null
  mlb_team: string | null
  status: string | null
  injury_status: string | null
  slot: string | null
  stat: PlayerStat | null
}

export interface StandingsRow {
  team_name: string
  owner_display_name: string | null
  is_my_team: boolean
  wins: number | null
  losses: number | null
  ties: number | null
  rank: number | null
}

export interface RankedPlayer {
  rank: number
  full_name: string
  position: string | null
  mlb_team: string | null
}

export interface Suggestion {
  kind: 'upgrade' | 'stash'
  position: string | null
  add_full_name: string
  add_detail: string
  drop_full_name: string | null
  drop_detail: string | null
  reason: string
}

export interface SuggestionsResponse {
  suggestions: Suggestion[]
  warnings: string[]
}
