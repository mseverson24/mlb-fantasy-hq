import axios from 'axios'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import * as authApi from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import * as platformAccountsApi from '../api/platformAccounts'
import type { RawDebugResult } from '../api/platformAccounts'
import type { PlatformAccount } from '../types/api'

const DEBUG_WINDOW = 15000

function buildBookmarklet(ingestToken: string): string {
  const src = `(function(){
    var API=${JSON.stringify(API_BASE_URL)};
    var TOKEN=${JSON.stringify(ingestToken)};
    var path=location.pathname;
    var page='league';
    if(path.indexOf('/standings')>=0) page='standings';
    else if(path.indexOf('/players')>=0) page='players';
    else if(path.indexOf('/teams')>=0) page='roster';
    fetch(API+'/platform-accounts/cbs/ingest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:TOKEN,page:page,html:document.documentElement.outerHTML})})
      .then(function(r){return r.json()})
      .then(function(d){alert((d.ok?'MLB FantasyHQ: ':'MLB FantasyHQ failed: ')+d.message)})
      .catch(function(e){alert('MLB FantasyHQ error: '+e)});
  })();`
  return `javascript:${encodeURIComponent(src)}`
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [accounts, setAccounts] = useState<PlatformAccount[]>([])
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [accountsError, setAccountsError] = useState<string | null>(null)

  const [leagueName, setLeagueName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [bookmarklet, setBookmarklet] = useState<{ leagueName: string; href: string } | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const bookmarkletLinkRef = useRef<HTMLAnchorElement>(null)

  const [adminError, setAdminError] = useState<string | null>(null)
  const [isBecomingAdmin, setIsBecomingAdmin] = useState(false)

  const [debugPage, setDebugPage] = useState('roster')
  const [debugOffset, setDebugOffset] = useState(0)
  const [debugResult, setDebugResult] = useState<RawDebugResult | null>(null)
  const [isDebugLoading, setIsDebugLoading] = useState(false)
  const [debugError, setDebugError] = useState<string | null>(null)
  const [copyLabel, setCopyLabel] = useState('Copy')
  const [debugFind, setDebugFind] = useState('')

  useEffect(() => {
    platformAccountsApi
      .listPlatformAccounts()
      .then(setAccounts)
      .finally(() => setIsLoadingAccounts(false))
  }, [])

  useEffect(() => {
    // React blocks `javascript:` URLs passed as a JSX href prop (throws on
    // click) -- set it via a plain DOM call instead, which it doesn't
    // intercept, so the bookmarklet actually works when dragged.
    if (bookmarkletLinkRef.current && bookmarklet) {
      bookmarkletLinkRef.current.setAttribute('href', bookmarklet.href)
    }
  }, [bookmarklet])

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
    setBookmarklet(null)
    setIsSubmitting(true)
    try {
      const result = await platformAccountsApi.connectCBSAccount(leagueName)
      setBookmarklet({ leagueName: result.leagueName, href: buildBookmarklet(result.ingestToken) })
      setAccounts(await platformAccountsApi.listPlatformAccounts())
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setError(typeof detail === 'string' ? detail : 'Could not connect — try again in a moment.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function fetchDebug(page: string, offset: number, find?: string) {
    setIsDebugLoading(true)
    setDebugError(null)
    try {
      const result = await platformAccountsApi.getCBSRawDebug(page, offset, find)
      setDebugResult(result)
      setDebugOffset(result.offset)
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
          CBS blocks plain requests from our server, even with a valid session cookie — this has been confirmed
          directly, not guessed at. So instead of pasting a cookie, this app gives you a bookmarklet: a button you
          drag to your bookmarks bar. Click it while you're on your own, already-logged-in CBS league pages, and it
          sends what your browser sees straight to this app — no password or cookie ever touches our server.
        </p>
        {error && <p className="form-error">{error}</p>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="leagueName">League name (the part of your league's URL before .baseball.cbssports.com)</label>
            <input
              id="leagueName"
              type="text"
              value={leagueName}
              onChange={(e) => setLeagueName(e.target.value)}
              placeholder="e.g. oldorchard"
              required
            />
          </div>
          <button type="submit" className="btn" disabled={isSubmitting}>
            {isSubmitting ? 'Connecting…' : 'Connect CBS league'}
          </button>
        </form>

        {bookmarklet && (
          <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
            <p style={{ color: 'var(--success)' }}>Connected "{bookmarklet.leagueName}"! Now drag this to your bookmarks bar:</p>
            <p style={{ marginBottom: '0.75rem' }}>
              <a
                ref={bookmarkletLinkRef}
                className="btn"
                style={{ display: 'inline-block', textDecoration: 'none' }}
                onClick={(e) => e.preventDefault()}
              >
                ⚾ Sync to MLB FantasyHQ
              </a>
            </p>
            <p className="muted" style={{ fontSize: '0.85rem' }}>
              Then go to <strong>oldorchard.baseball.cbssports.com</strong>-style league pages in your own browser —
              your league home, My Team/roster, Standings, Players — while logged in, and click that bookmark on
              each one. It detects which page you're on automatically.
            </p>
            <p className="muted" style={{ fontSize: '0.85rem' }}>
              For pickup suggestions on the Pickups page, click it on the Players page filtered to{' '}
              <strong>Free Agents</strong> — that's what the suggestions treat as "available."
            </p>
          </div>
        )}
      </div>

      <div className="card">
        <h2>CBS raw HTML debug</h2>
        <p className="muted" style={{ fontSize: '0.85rem' }}>
          Shows whatever the bookmarklet last sent for each page type. Requires a connected CBS account above and at
          least one bookmarklet click.
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
            {isDebugLoading ? 'Loading…' : 'View'}
          </button>
        </div>
        <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.75rem' }}>
          <input
            type="text"
            value={debugFind}
            onChange={(e) => setDebugFind(e.target.value)}
            placeholder="jump to text, e.g. a player name or <table"
            style={{ flex: 1 }}
          />
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => fetchDebug(debugPage, 0, debugFind)}
            disabled={isDebugLoading || !debugFind}
          >
            Find
          </button>
        </div>

        {debugResult && (
          <div>
            <p className="muted" style={{ fontSize: '0.85rem' }}>
              status: {debugResult.status}
              {debugResult.total_length !== null && <> · total length: {debugResult.total_length}</>} · offset:{' '}
              {debugResult.offset}
              {debugResult.ingested_at && <> · ingested: {new Date(debugResult.ingested_at).toLocaleString()}</>}
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
