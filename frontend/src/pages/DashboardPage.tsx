import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import * as leaguesApi from '../api/leagues'
import type { League } from '../types/api'

export default function DashboardPage() {
  const [leagues, setLeagues] = useState<League[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    leaguesApi
      .listLeagues()
      .then(setLeagues)
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <div className="page-loading">Loading…</div>

  return (
    <div>
      <h1>Dashboard</h1>
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
            <Link to="/roster" className="btn btn-secondary">
              View my team
            </Link>
          </div>
        ))
      )}
    </div>
  )
}
