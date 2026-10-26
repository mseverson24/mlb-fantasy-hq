import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as leaguesApi from '../api/leagues'
import type { League } from '../types/api'

export default function DashboardPage() {
  const [leagues, setLeagues] = useState<League[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [syncingId, setSyncingId] = useState<string | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)

  useEffect(() => {
    leaguesApi
      .listLeagues()
      .then(setLeagues)
      .finally(() => setIsLoading(false))
  }, [])

  async function handleSync(leagueId: string) {
    setSyncError(null)
    setSyncingId(leagueId)
    try {
      const updated = await leaguesApi.syncLeague(leagueId)
      setLeagues((prev) => prev.map((l) => (l.id === leagueId ? updated : l)))
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setSyncError(typeof detail === 'string' ? detail : 'Could not sync — use the bookmarklet from Settings first.')
    } finally {
      setSyncingId(null)
    }
  }

  if (isLoading) return <div className="page-loading">Loading…</div>

  return (
    <div>
      <h1>Dashboard</h1>
      {syncError && <p className="form-error">{syncError}</p>}
      {leagues.length === 0 ? (
        <div className="card">
          <p>No league connected yet.</p>
          <Link to="/settings" className="btn">
            Connect your CBS league
          </Link>
        </div>
      ) : (
        leagues.map((league) => (
          <div key={league.id} className="card league-card">
            <div>
              <h3>{league.name}</h3>
              <p className="muted">
                {league.season} season
                {league.num_teams ? ` · ${league.num_teams} teams` : ''}
                {league.last_synced_at
                  ? ` · synced ${new Date(league.last_synced_at).toLocaleString()}`
                  : ' · not yet synced'}
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn-link"
                onClick={() => handleSync(league.id)}
                disabled={syncingId === league.id}
              >
                {syncingId === league.id ? 'Syncing…' : 'Sync'}
              </button>
              <Link to="/roster" className="btn btn-secondary">
                View my team
              </Link>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
