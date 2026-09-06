import Wordmark from './Wordmark'

/**
 * The signed-in header.
 *
 * Entirely props-driven - no context - so it can be rendered and inspected
 * without a live session, and so the identity line and the controls can't
 * quietly start depending on each other.
 *
 * Layout is two rows on purpose: the wordmark and the controls people act on
 * share the top row, and the things people only read - who they're signed in
 * as, how fresh the rates are - sit beneath in smaller muted type rather than
 * competing with buttons for the same line.
 */
export default function DashboardHeader({ email, meta, controls, onSignOut }) {
  return (
    <header className="dashboard-header">
      <div className="dashboard-bar">
        <Wordmark />
        <div className="dashboard-controls">
          {controls}
          <button className="btn secondary" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </div>
      {(email || meta) && (
        <p className="dashboard-meta">
          {email}
          {email && meta ? <span className="dot"> · </span> : null}
          {meta}
        </p>
      )}
    </header>
  )
}
