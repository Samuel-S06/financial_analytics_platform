import Dashboard from './components/Dashboard'
import Landing from './components/Landing'
import { AuthProvider, useAuth } from './context/AuthContext'

/**
 * The gate: signed out sees the landing page, signed in sees the dashboard.
 *
 * Split from App so it can call useAuth - a component can't consume a context
 * its own render provides.
 */
function Gate() {
  const { session, loading } = useAuth()

  // Supabase restores the session from localStorage asynchronously. Rendering
  // the landing page during that window would flash it at a signed-in user.
  if (loading) {
    return (
      <div className="app boot">
        <span className="spinner" />
      </div>
    )
  }

  return <div className="app">{session ? <Dashboard /> : <Landing />}</div>
}

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  )
}
