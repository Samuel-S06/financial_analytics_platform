import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import LandingPreview from './LandingPreview'
import Wordmark from './Wordmark'
import { isSupabaseConfigured } from '../lib/supabase'

// Four blurred shapes drifting behind the hero. Drift on all of them; a slow
// breath on only two - pulsing everything at once reads as busy, which is the
// opposite of the intent.
const SHAPES = [
  { id: 'a', drift: { x: [0, 30, 0], y: [0, -20, 0] }, pulse: [1, 1.06, 1], duration: 19 },
  { id: 'b', drift: { x: [0, -26, 0], y: [0, 22, 0] }, pulse: null, duration: 23 },
  { id: 'c', drift: { x: [0, 18, 0], y: [0, 26, 0] }, pulse: [1, 1.05, 1], duration: 27 },
  { id: 'd', drift: { x: [0, -22, 0], y: [0, -16, 0] }, pulse: null, duration: 21 },
]

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
/**
 * Entrance choreography.
 *
 * Each element states its own delay rather than inheriting a staggerChildren
 * cascade. The sequence is deliberate - wordmark, headline, subtext, the
 * sample card, then the form - and DOM order no longer silently decides it,
 * so moving markup around can't reshuffle the timing.
 *
 * Under prefers-reduced-motion every distance collapses to zero and only
 * opacity is left: the sequence still reads, nothing moves.
 */
const BEAT = 0.1

const container = { hidden: {}, shown: {} }

const rise = (reduced, delay = 0) => ({
  hidden: { opacity: 0, y: reduced ? 0 : 18 },
  shown: {
    opacity: 1,
    y: 0,
    transition: reduced
      ? { duration: 0.2, delay: 0 }
      // Springs rather than eases: the arrival settles instead of stopping dead.
      : { type: 'spring', stiffness: 260, damping: 26, mass: 0.9, delay },
  },
})

// The form is the thing we want people to reach, so it arrives last and with
// the most personality: a low overshoot - stiff spring, light damping - reads
// as a small hop rather than a slide.
const hop = (reduced, delay = 0) => ({
  hidden: { opacity: 0, y: reduced ? 0 : 44, scale: reduced ? 1 : 0.97 },
  shown: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: reduced
      ? { duration: 0.2 }
      : { type: 'spring', stiffness: 320, damping: 17, mass: 0.85, delay },
  },
})

// The feature blurbs are below the fold, so they wait for the reader rather
// than firing on load where nobody sees them.
const revealOnScroll = (reduced, index) => ({
  initial: { opacity: 0, y: reduced ? 0 : 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.6 },
  transition: reduced
    ? { duration: 0.2 }
    : { duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: index * 0.09 },
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

  // This project keeps Supabase's "Confirm email" on, so a new account has no
  // session until it's confirmed. Both messages end at the sign-in form, so
  // they say that plainly rather than leaving a dead end. Neither names the
  // auth provider: how the account gets confirmed is our problem, not the
  // reader's.
  const CONFIRM_REQUIRED =
    'Account created. Confirm it from the email we sent, then sign in below.'
  const NOT_CONFIRMED =
    'This account still needs confirming. Use the link in your signup email, ' +
    'then try again.'

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
        // Supabase reports this as a plain "Email not confirmed", which tells
        // the user nothing about what to do next.
        const unconfirmed =
          authError.code === 'email_not_confirmed' ||
          /not confirmed/i.test(authError.message)
        setError(unconfirmed ? NOT_CONFIRMED : authError.message)
      } else if (mode === 'signup' && !data.session) {
        // Confirmation is required: the user exists but has no session yet.
        // Move them to the sign-in tab with the email still filled in, so
        // signing in after confirming is one click and one password.
        setMode('signin')
        setPassword('')
        setNotice(CONFIRM_REQUIRED)
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
      variants={container}
      initial="hidden"
      animate="shown"
    >
      <div className="landing-top on-field">
        {/* Decorative depth behind the hero: a full-bleed wash plus four
            blurred shapes. Only transform and opacity animate - moving the
            blur radius itself would force a repaint of a very large blurred
            surface every frame and judder. Hidden from assistive tech, and
            held still under reduced motion. */}
        <div className="landing-atmosphere" aria-hidden="true">
          {SHAPES.map(({ id, drift, pulse, duration }) => (
            <motion.span
              key={id}
              className={`shape shape-${id}`}
              animate={reduced ? {} : {
                x: drift.x,
                y: drift.y,
                ...(pulse ? { scale: pulse } : {}),
              }}
              transition={{ duration, repeat: Infinity, ease: 'easeInOut' }}
            />
          ))}
        </div>

        <motion.div variants={rise(reduced, 0)}>
          <Wordmark />
        </motion.div>

        <section className="hero">
          <motion.h1 className="hero-title" variants={rise(reduced, BEAT)}>
            Know where the money went.
          </motion.h1>
          <motion.p className="hero-subtitle" variants={rise(reduced, BEAT * 1.6)}>
            Upload a transaction CSV and get a spending breakdown, a month-by-month
            trend, and a savings plan you can actually hit.
          </motion.p>
        </section>

        <div className="card-stage">
          <div className="landing-grid">
            <LandingPreview delay={BEAT * 2.4} />

            <motion.div className="card auth-card" variants={hop(reduced, BEAT * 3.4)}>
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
        </div>
      </div>

      <ul className="feature-strip">
        {FEATURES.map(([title, body], i) => (
          <motion.li className="feature" key={title} {...revealOnScroll(reduced, i)}>
            <h3>{title}</h3>
            <p>{body}</p>
          </motion.li>
        ))}
      </ul>

      <motion.footer className="landing-footer" {...revealOnScroll(reduced, 3)}>
        Made with love by Samuel Sosa © 2026
      </motion.footer>
    </motion.div>
  )
}
