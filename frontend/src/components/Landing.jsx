import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { isSupabaseConfigured } from '../lib/supabase'

const FEATURES = [
  ['Upload a CSV', 'Drop in a bank export. Bad rows are cleaned and reported, not silently dropped.'],
  ['See where it goes', 'Spending by category and month, from the first upload.'],
  ['Test a savings goal', 'Pick a target and the categories to cut from; get a monthly budget back.'],
]

/**
 * Entrance choreography.
 *
 * One parent orchestrates the whole page: children inherit the "hidden" and
 * "shown" names, so each element's own variants decide how it arrives while
 * the parent decides when. That keeps the timing in one place instead of
 * scattered delays that drift apart whenever the markup changes.
 *
 * Under prefers-reduced-motion every distance and blur collapses to zero and
 * only opacity is left - the sequence still reads, nothing moves.
 */
const container = (reduced) => ({
  hidden: {},
  shown: {
    transition: {
      staggerChildren: reduced ? 0.04 : 0.09,
      delayChildren: reduced ? 0 : 0.08,
    },
  },
})

const rise = (reduced) => ({
  hidden: { opacity: 0, y: reduced ? 0 : 18 },
  shown: {
    opacity: 1,
    y: 0,
    transition: reduced
      ? { duration: 0.2 }
      // Springs rather than eases: the arrival settles instead of stopping
      // dead, which is what makes it read as physical.
      : { type: 'spring', stiffness: 260, damping: 26, mass: 0.9 },
  },
})

const slideIn = (reduced) => ({
  hidden: { opacity: 0, x: reduced ? 0 : 24 },
  shown: {
    opacity: 1,
    x: 0,
    transition: reduced
      ? { duration: 0.2 }
      : { type: 'spring', stiffness: 220, damping: 28, delay: 0.12 },
  },
})

export default function Landing() {
  const { signIn, signUp } = useAuth()
  const reduced = useReducedMotion()
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [busy, setBusy] = useState(false)

  const switchMode = (next) => {
    setMode(next)
    setError(null)
    setNotice(null)
  }

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
VITE_SUPABASE_ANON_KEY=<publishable key>`}
          </pre>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className="landing"
      variants={container(reduced)}
      initial="hidden"
      animate="shown"
    >
      {/* Two slow-drifting washes behind the hero. Decorative only, so it is
          hidden from assistive tech, and it holds still under reduced motion. */}
      <div className="landing-glow" aria-hidden="true">
        <motion.span
          className="glow glow-a"
          animate={reduced ? {} : { x: [0, 28, 0], y: [0, -18, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.span
          className="glow glow-b"
          animate={reduced ? {} : { x: [0, -24, 0], y: [0, 20, 0] }}
          transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <section className="hero">
        <motion.h1 className="hero-title" variants={rise(reduced)}>
          Know where the money went.
        </motion.h1>
        <motion.p className="hero-subtitle" variants={rise(reduced)}>
          Upload a transaction CSV and get a spending breakdown, a month-by-month
          trend, and a savings plan you can actually hit.
        </motion.p>
      </section>

      <div className="landing-grid">
        <ul className="feature-list">
          {FEATURES.map(([title, body]) => (
            <motion.li className="feature" key={title} variants={rise(reduced)}>
              <h3>{title}</h3>
              <p>{body}</p>
            </motion.li>
          ))}
        </ul>

        <motion.div className="card auth-card" variants={slideIn(reduced)}>
          <div className="auth-tabs" role="tablist">
            {[['signin', 'Sign in'], ['signup', 'Create account']].map(([key, label]) => (
              <button
                key={key}
                role="tab"
                aria-selected={mode === key}
                className={`auth-tab ${mode === key ? 'active' : ''}`}
                onClick={() => switchMode(key)}
              >
                {label}
                {/* One shared layoutId means the underline travels between
                    tabs instead of disappearing and reappearing. */}
                {mode === key && (
                  <motion.span
                    className="auth-tab-underline"
                    layoutId="auth-tab-underline"
                    transition={reduced
                      ? { duration: 0 }
                      : { type: 'spring', stiffness: 380, damping: 32 }}
                  />
                )}
              </button>
            ))}
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

            {/* Messages animate their own height so the card grows into the
                space rather than snapping and shifting the button underfoot. */}
            <AnimatePresence initial={false}>
              {(error || notice) && (
                <motion.div
                  key={error ? 'error' : 'notice'}
                  className={`status-banner ${error ? 'error' : 'info'}`}
                  initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                  animate={{ opacity: 1, height: 'auto', marginBottom: 16 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  transition={{ duration: reduced ? 0 : 0.22 }}
                >
                  {error || notice}
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button
              className="btn auth-submit"
              type="submit"
              disabled={busy}
              whileHover={reduced || busy ? {} : { scale: 1.015 }}
              whileTap={reduced || busy ? {} : { scale: 0.985 }}
            >
              {busy
                ? <><span className="spinner" /> Working...</>
                : mode === 'signup' ? 'Create account' : 'Sign in'}
            </motion.button>
          </form>
        </motion.div>
      </div>
    </motion.div>
  )
}
