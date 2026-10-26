import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as leaguesApi from '../api/leagues'
import PositionBadge from '../components/PositionBadge'
import type { League, Suggestion } from '../types/api'

export default function PickupsPage() {
  const [league, setLeague] = useState<League | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [warnings, setWarnings] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    leaguesApi
      .listLeagues()
      .then(async (leagues) => {
        if (leagues.length === 0) return
        setLeague(leagues[0])
        const result = await leaguesApi.getSuggestions(leagues[0].id)
        setSuggestions(result.suggestions)
        setWarnings(result.warnings)
      })
      .catch(() => setError('Could not load pickup suggestions right now — try again later.'))
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

  const upgrades = suggestions.filter((s) => s.kind === 'upgrade')
  const stashes = suggestions.filter((s) => s.kind === 'stash')

  return (
    <div>
      <h1>Pickups — {league.name}</h1>
      <p className="muted">
        Upgrades compare your roster against players synced from CBS's Players page (filtered to Free Agents gets
        the best results). Stashes are MLB Pipeline prospects not yet on CBS's player list at all.
      </p>
      {error && <p className="form-error">{error}</p>}
      {warnings.map((w) => (
        <p key={w} className="form-error">
          {w}
        </p>
      ))}

      <div className="card">
        <h2>Roster upgrades</h2>
        {upgrades.length === 0 ? (
          <p className="muted">No clear upgrades found right now.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Add</th>
                <th>Drop</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {upgrades.map((s) => (
                <tr key={`${s.kind}-${s.add_full_name}`}>
                  <td>
                    <PositionBadge position={s.position} />
                  </td>
                  <td>
                    {s.add_full_name}
                    <div className="muted" style={{ fontSize: '0.8rem' }}>
                      {s.add_detail}
                    </div>
                  </td>
                  <td>
                    {s.drop_full_name}
                    <div className="muted" style={{ fontSize: '0.8rem' }}>
                      {s.drop_detail}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{s.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2>Prospect stashes</h2>
        {stashes.length === 0 ? (
          <p className="muted">No matching stash candidates right now.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Prospect</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {stashes.map((s) => (
                <tr key={`${s.kind}-${s.add_full_name}`}>
                  <td>
                    <PositionBadge position={s.position} />
                  </td>
                  <td>
                    {s.add_full_name}
                    <div className="muted" style={{ fontSize: '0.8rem' }}>
                      {s.add_detail}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{s.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
