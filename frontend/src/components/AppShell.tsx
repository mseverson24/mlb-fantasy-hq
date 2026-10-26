import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? 'app-nav-link active' : 'app-nav-link'
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="app-nav">
        <div className="app-nav-inner">
          <NavLink to="/" end className="app-brand">
            ⚾ MLB FantasyHQ
          </NavLink>
          <nav className="app-nav-links">
            <NavLink to="/" end className={navLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/roster" className={navLinkClass}>
              My Team
            </NavLink>
            <NavLink to="/standings" className={navLinkClass}>
              Standings
            </NavLink>
            <NavLink to="/rankings" className={navLinkClass}>
              Rankings
            </NavLink>
            <NavLink to="/pickups" className={navLinkClass}>
              Pickups
            </NavLink>
            <NavLink to="/settings" className={navLinkClass}>
              Settings
            </NavLink>
          </nav>
          <div className="app-nav-user">
            <span className="muted">{user?.display_name}</span>
            <button type="button" className="btn btn-secondary" onClick={logout}>
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="app-content">{children}</main>
    </div>
  )
}
