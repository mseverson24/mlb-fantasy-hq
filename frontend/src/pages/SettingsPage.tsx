import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import * as authApi from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import * as platformAccountsApi from '../api/platformAccounts'
import type { League, PlatformAccount } from '../types/api'

export default function SettingsPage() {
  const { user } = useAuth()
  const [accounts, setAccounts] = useState<PlatformAccount[]>([])
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [leagueName, setLeagueName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [connectedLeague, setConnectedLeague] = useState<League | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [adminError, setAdminError] = useState<string | null>(null)
  const [isBecomingAdmin, setIsBecomingAdmin] = useState(false)

  useEffect(() => {
    platformAccountsApi
      .listPlatformAccounts()
      .then(setAccounts)
      .finally(() => setIsLoadingAccounts(false))
  }, [])

  async function handleBecomeAdmin() {
    setAdminError(null)
    setIsBecomingAdmin(true)
    try {
      await authApi.bootstrapAdmin()
      window.location.reload()
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setAdminError(typeof detail === 'string' ? detail : 'Could not set admin status.')
      setIsBecomingAdmin(false)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setConnectedLeague(null)
    setIsSubmitting(true)
    try {
      const league = await platformAccountsApi.linkCBSAccount(username, password, leagueName)
      setConnectedLeague(league)
      setAccounts(await platformAccountsApi.listPlatformAccounts())
      setPassword('')
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setError(typeof detail === 'string' ? detail : 'Could not connect to CBS — try again in a moment.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      <h1>Settings</h1>

      {!user?.is_admin && (
        <div className="card">
          <h2>Admin access</h2>
          <p className="muted">
            No admin exists yet on this app. The first person to click this becomes admin — it stops working the
            moment anyone does.
          </p>
          {adminError && <p className="form-error">{adminError}</p>}
          <button type="button" className="btn btn-secondary" onClick={handleBecomeAdmin} disabled={isBecomingAdmin}>
            {isBecomingAdmin ? 'Setting…' : 'Become admin'}
          </button>
        </div>
      )}

      <div className="card">
        <h2>Connected accounts</h2>
        {isLoadingAccounts ? (
          <p className="muted">Loading…</p>
        ) : accounts.length === 0 ? (
          <p className="muted">No accounts connected yet.</p>
        ) : (
          <ul>
            {accounts.map((a) => (
              <li key={a.id}>
                {a.platform.toUpperCase()} — {a.display_name} {a.is_connected ? '(connected)' : '(not connected)'}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card">
        <h2>Connect your CBS league</h2>
        <p className="muted">
          CBS Fantasy has no official login system for apps like this one — your password is used once, right
          now, to sign in and is never stored. Only the resulting session is kept, the same way this works for
          other password-based platforms.
        </p>
        {error && <p className="form-error">{error}</p>}
        {connectedLeague && (
          <p style={{ color: 'var(--success)' }}>
            Connected! Found "{connectedLeague.name}" ({connectedLeague.season}).
          </p>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="leagueName">
              League name (the part of your league's URL before .cbssports.com)
            </label>
            <input
              id="leagueName"
              type="text"
              value={leagueName}
              onChange={(e) => setLeagueName(e.target.value)}
              placeholder="e.g. myleague"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="username">CBS username or email</label>
            <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label htmlFor="password">CBS password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn" disabled={isSubmitting}>
            {isSubmitting ? 'Connecting…' : 'Connect CBS account'}
          </button>
        </form>
      </div>
    </div>
  )
}
