import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as leaguesApi from '../api/leagues'
import type { League, StandingsRow } from '../types/api'

export default function StandingsPage() {
  const [league, setLeague] = useState<League | null>(null)
  const [rows, setRows] = useState<StandingsRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    leaguesApi
      .listLeagues()
      .then(async (leagues) => {
        if (leagues.length === 0) return
        setLeague(leagues[0])
        setRows(await leaguesApi.getStandings(leagues[0].id))
      })
      .catch(() => setError('Could not load standings'))
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
      <h1>Standings — {league.name}</h1>
      {error && <p className="form-error">{error}</p>}
      {rows.length === 0 && !error ? (
        <p className="muted">No standings data yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Team</th>
              <th>W</th>
              <th>L</th>
              <th>T</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.team_name}>
                <td>{r.rank ?? '—'}</td>
                <td>{r.team_name} {r.is_my_team && <strong>(you)</strong>}</td>
                <td>{r.wins ?? '—'}</td>
                <td>{r.losses ?? '—'}</td>
                <td>{r.ties ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
