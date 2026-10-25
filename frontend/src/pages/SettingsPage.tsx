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

  const [leagueName, setLeagueName] = useState('')
  const [authSession, setAuthSession] = useState('')
  const [authState, setAuthState] = useState('')
  const [awsAlb, setAwsAlb] = useState('')
  const [awsAlbCors, setAwsAlbCors] = useState('')
  const [showExtraCookies, setShowExtraCookies] = useState(false)
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
      const league = await platformAccountsApi.linkCBSAccount({
        leagueName,
        authSession,
        authState,
        awsAlb,
        awsAlbCors,
      })
      setConnectedLeague(league)
      setAccounts(await platformAccountsApi.listPlatformAccounts())
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
          CBS has no login system an app like this can sign in through directly — their site doesn't work that
          way anymore. Instead: log into CBS normally in your own browser, open developer tools (F12, or
          right-click → Inspect), go to <strong>Application → Cookies → cbssports.com</strong>, find the cookie
          named <strong>auth_session</strong>, and paste its value below. Nothing is typed into this app except
          that one cookie value — no CBS password, ever.
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
            <label htmlFor="authSession">auth_session cookie value</label>
            <input
              id="authSession"
              type="text"
              value={authSession}
              onChange={(e) => setAuthSession(e.target.value)}
              required
            />
          </div>

          {!showExtraCookies ? (
            <button type="button" className="btn-link" onClick={() => setShowExtraCookies(true)} style={{ marginBottom: '0.75rem' }}>
              Connection failed? Add more cookies
            </button>
          ) : (
            <>
              <p className="muted" style={{ fontSize: '0.85rem' }}>
                Only needed if connecting fails with just auth_session — grab these from the same cookie list.
              </p>
              <div className="form-group">
                <label htmlFor="authState">auth_state cookie value (optional)</label>
                <input id="authState" type="text" value={authState} onChange={(e) => setAuthState(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="awsAlb">AWSALB cookie value (optional)</label>
                <input id="awsAlb" type="text" value={awsAlb} onChange={(e) => setAwsAlb(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="awsAlbCors">AWSALBCORS cookie value (optional)</label>
                <input id="awsAlbCors" type="text" value={awsAlbCors} onChange={(e) => setAwsAlbCors(e.target.value)} />
              </div>
            </>
          )}

          <button type="submit" className="btn" disabled={isSubmitting}>
            {isSubmitting ? 'Connecting…' : 'Connect CBS account'}
          </button>
        </form>
      </div>
    </div>
  )
}
