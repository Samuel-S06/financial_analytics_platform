import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { isSupabaseConfigured } from '../lib/supabase'

const FEATURES = [
  ['Upload a CSV', 'Drop in a bank export. Bad rows are cleaned and reported, not silently dropped.'],
  ['See where it goes', 'Spending by category and month, from the first upload.'],
  ['Test a savings goal', 'Pick a target and the categories to cut from; get a monthly budget back.'],
]

/**
 * The signed-out view: what the app does, plus sign-up / sign-in.
 *
 * Structure only at this point - the entrance animation lands on top of this
 * markup, so the element order here is also the order things animate in.
 */
export default function Landing() {
  const { signIn, signUp } = useAuth()
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setNotice(null)
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setBusy(true)
    try {
      const action = mode === 'signup' ? signUp : signIn
      const { data, error: authError } = await action(email, password)
      if (authError) {
        setError(authError.message)
      } else if (mode === 'signup' && !data.session) {
        // Happens when the project has email confirmation switched on: the
        // user exists but has no session until they click the link.
        setNotice('Check your email to confirm your account, then sign in.')
      }
      // On success there's nothing to do - the auth listener swaps the view.
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!isSupabaseConfigured) {
    return (
      <div className="landing">
        <div className="card">
          <h2>Supabase isn't configured yet</h2>
          <p className="card-subtitle">
            Create <code>frontend/.env.local</code> with your project's URL and
            anon key, then restart the dev server:
          </p>
          <pre className="code-block">
{`VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key>`}
          </pre>
        </div>
      </div>
    )
  }

  return (
    <div className="landing">
      <section className="hero">
        <h1 className="hero-title">Know where the money went.</h1>
        <p className="hero-subtitle">
          Upload a transaction CSV and get a spending breakdown, a month-by-month
          trend, and a savings plan you can actually hit.
        </p>
      </section>

      <div className="landing-grid">
        <ul className="feature-list">
          {FEATURES.map(([title, body]) => (
            <li className="feature" key={title}>
              <h3>{title}</h3>
              <p>{body}</p>
            </li>
          ))}
        </ul>

        <div className="card auth-card">
          <div className="auth-tabs" role="tablist">
            <button
              role="tab"
              aria-selected={mode === 'signin'}
              className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
              onClick={() => { setMode('signin'); setError(null); setNotice(null) }}
            >
              Sign in
            </button>
            <button
              role="tab"
              aria-selected={mode === 'signup'}
              className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => { setMode('signup'); setError(null); setNotice(null) }}
            >
              Create account
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && <div className="status-banner error">{error}</div>}
            {notice && <div className="status-banner info">{notice}</div>}

            <button className="btn auth-submit" type="submit" disabled={busy}>
              {busy
                ? <><span className="spinner" /> Working...</>
                : mode === 'signup' ? 'Create account' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
