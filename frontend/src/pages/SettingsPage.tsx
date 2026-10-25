import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import * as authApi from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import * as platformAccountsApi from '../api/platformAccounts'
import type { RawDebugResult } from '../api/platformAccounts'
import type { League, PlatformAccount } from '../types/api'

const DEBUG_WINDOW = 15000

export default function SettingsPage() {
  const { user } = useAuth()
  const [accounts, setAccounts] = useState<PlatformAccount[]>([])
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [accountsError, setAccountsError] = useState<string | null>(null)

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

  const [debugPage, setDebugPage] = useState('roster')
  const [debugOffset, setDebugOffset] = useState(0)
  const [debugResult, setDebugResult] = useState<RawDebugResult | null>(null)
  const [isDebugLoading, setIsDebugLoading] = useState(false)
  const [debugError, setDebugError] = useState<string | null>(null)
  const [copyLabel, setCopyLabel] = useState('Copy')

  useEffect(() => {
    platformAccountsApi
      .listPlatformAccounts()
      .then(setAccounts)
      .finally(() => setIsLoadingAccounts(false))
  }, [])

  async function handleDeleteAccount(account: PlatformAccount) {
    if (!window.confirm(`Remove ${account.platform.toUpperCase()} — ${account.display_name}?`)) return
    setAccountsError(null)
    setDeletingId(account.id)
    try {
      await platformAccountsApi.deletePlatformAccount(account.id)
      setAccounts((prev) => prev.filter((a) => a.id !== account.id))
      setDebugResult(null)
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setAccountsError(typeof detail === 'string' ? detail : 'Could not remove that account.')
    } finally {
      setDeletingId(null)
    }
  }

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

  async function fetchDebug(page: string, offset: number) {
    setIsDebugLoading(true)
    setDebugError(null)
    try {
      const result = await platformAccountsApi.getCBSRawDebug(page, offset)
      setDebugResult(result)
      setDebugOffset(offset)
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setDebugError(typeof detail === 'string' ? detail : 'Could not fetch debug HTML.')
    } finally {
      setIsDebugLoading(false)
    }
  }

  function handleCopySnippet() {
    const text = debugResult?.html_snippet ?? ''
    if (!text) return
    if (navigator.clipboard?.writeText) {
      navigator.clipboard
        .writeText(text)
        .then(() => setCopyLabel('Copied!'))
        .catch(() => setCopyLabel('Copy failed'))
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        setCopyLabel('Copied!')
      } catch {
        setCopyLabel('Copy failed')
      }
      document.body.removeChild(textarea)
    }
    setTimeout(() => setCopyLabel('Copy'), 2000)
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
        {accountsError && <p className="form-error">{accountsError}</p>}
        {isLoadingAccounts ? (
          <p className="muted">Loading…</p>
        ) : accounts.length === 0 ? (
          <p className="muted">No accounts connected yet.</p>
        ) : (
          <ul>
            {accounts.map((a) => (
              <li key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <span>
                  {a.platform.toUpperCase()} — {a.display_name} {a.is_connected ? '(connected)' : '(not connected)'}
                </span>
                <button
                  type="button"
                  className="btn-link"
                  style={{ color: 'var(--danger)' }}
                  onClick={() => handleDeleteAccount(a)}
                  disabled={deletingId === a.id}
                >
                  {deletingId === a.id ? 'Removing…' : 'Remove'}
                </button>
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

      <div className="card">
        <h2>CBS raw HTML debug</h2>
        <p className="muted" style={{ fontSize: '0.85rem' }}>
          Temporary tool for diagnosing CBS page structure. Requires a connected CBS account above.
        </p>
        {debugError && <p className="form-error">{debugError}</p>}
        <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.75rem' }}>
          <select
            value={debugPage}
            onChange={(e) => setDebugPage(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-h)',
              padding: '0.5rem 0.6rem',
            }}
          >
            <option value="roster">roster</option>
            <option value="league">league</option>
            <option value="standings">standings</option>
            <option value="players">players</option>
          </select>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => fetchDebug(debugPage, 0)}
            disabled={isDebugLoading}
          >
            {isDebugLoading ? 'Fetching…' : 'Fetch'}
          </button>
        </div>

        {debugResult && (
          <div>
            <p className="muted" style={{ fontSize: '0.85rem' }}>
              status: {debugResult.status}
              {debugResult.total_length !== null && <> · total length: {debugResult.total_length}</>} · offset:{' '}
              {debugResult.offset}
            </p>
            {debugResult.error && <p className="form-error">{debugResult.error}</p>}
            {debugResult.html_snippet !== null && (
              <>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={isDebugLoading || debugOffset <= 0}
                    onClick={() => fetchDebug(debugPage, Math.max(0, debugOffset - DEBUG_WINDOW))}
                  >
                    ← Prev
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={
                      isDebugLoading ||
                      (debugResult.total_length !== null && debugOffset + DEBUG_WINDOW >= debugResult.total_length)
                    }
                    onClick={() => fetchDebug(debugPage, debugOffset + DEBUG_WINDOW)}
                  >
                    Next →
                  </button>
                  <button type="button" className="btn-link" onClick={handleCopySnippet}>
                    {copyLabel}
                  </button>
                </div>
                <pre
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.75rem',
                    maxHeight: '400px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    fontSize: '0.75rem',
                  }}
                >
                  {debugResult.html_snippet}
                </pre>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
