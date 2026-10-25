import { useEffect, useState } from 'react'
import * as rankingsApi from '../api/rankings'
import PositionBadge from '../components/PositionBadge'
import type { RankedPlayer } from '../types/api'

export default function RankingsPage() {
  const [rankings, setRankings] = useState<RankedPlayer[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    rankingsApi
      .getRankings()
      .then(setRankings)
      .catch(() => setError('Could not load rankings right now — try again later.'))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <div className="page-loading">Loading…</div>

  return (
    <div>
      <h1>MLB Rankings</h1>
      <p className="muted">Overall fantasy baseball rankings (CBS Sports, public — no CBS login needed here).</p>
      {error && <p className="form-error">{error}</p>}
      {rankings.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Player</th>
              <th>Pos</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((r) => (
              <tr key={r.rank}>
                <td>{r.rank}</td>
                <td>{r.full_name}</td>
                <td>
                  <PositionBadge position={r.position} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
