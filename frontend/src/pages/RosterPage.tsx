import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as leaguesApi from '../api/leagues'
import PositionBadge from '../components/PositionBadge'
import type { League, RosterPlayer } from '../types/api'

function formatStat(player: RosterPlayer): string {
  const s = player.stat
  if (!s) return '—'
  const isPitcher = player.position === 'SP' || player.position === 'RP'
  if (isPitcher) {
    return s.era != null ? `${s.wins ?? 0}-${s.losses ?? 0}, ${s.era.toFixed(2)} ERA, ${s.strikeouts ?? 0} K` : '—'
  }
  return s.batting_avg != null
    ? `.${Math.round(s.batting_avg * 1000)
        .toString()
        .padStart(3, '0')}, ${s.home_runs ?? 0} HR, ${s.rbi ?? 0} RBI`
    : '—'
}

export default function RosterPage() {
  const [league, setLeague] = useState<League | null>(null)
  const [roster, setRoster] = useState<RosterPlayer[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    leaguesApi
      .listLeagues()
      .then(async (leagues) => {
        if (leagues.length === 0) return
        setLeague(leagues[0])
        setRoster(await leaguesApi.getMyRoster(leagues[0].id))
      })
      .catch(() => setError('Could not load your roster'))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <div className="page-loading">Loading…</div>

  if (!league) {
    return (
      <div className="card">
        <p>No league connected yet.</p>
        <Link to="/settings" className="btn">
          Connect your CBS league
        </Link>
      </div>
    )
  }

  return (
    <div>
      <h1>My Team — {league.name}</h1>
      {error && <p className="form-error">{error}</p>}
      {roster.length === 0 ? (
        <p className="muted">No roster data yet — try syncing from the Dashboard.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Slot</th>
              <th>Player</th>
              <th>Pos</th>
              <th>Team</th>
              <th>Status</th>
              <th>Stats</th>
            </tr>
          </thead>
          <tbody>
            {roster.map((p) => (
              <tr key={p.player_id}>
                <td>{p.slot ?? '—'}</td>
                <td>{p.full_name}</td>
                <td>
                  <PositionBadge position={p.position} />
                </td>
                <td>{p.mlb_team ?? '—'}</td>
                <td>{p.injury_status ?? p.status ?? '—'}</td>
                <td>{formatStat(p)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
