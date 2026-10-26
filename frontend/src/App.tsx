import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import AppShell from './components/AppShell'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import PickupsPage from './pages/PickupsPage'
import RankingsPage from './pages/RankingsPage'
import RegisterPage from './pages/RegisterPage'
import RosterPage from './pages/RosterPage'
import SettingsPage from './pages/SettingsPage'
import StandingsPage from './pages/StandingsPage'
import './App.css'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div className="page-loading">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return <AppShell>{children}</AppShell>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/roster"
        element={
          <ProtectedRoute>
            <RosterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/standings"
        element={
          <ProtectedRoute>
            <StandingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/rankings"
        element={
          <ProtectedRoute>
            <RankingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pickups"
        element={
          <ProtectedRoute>
            <PickupsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
