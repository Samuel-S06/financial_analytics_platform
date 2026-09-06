import { Component } from 'react'

/**
 * Catches render-time errors anywhere below it.
 *
 * Without this, one thrown error unmounts the whole tree and the page goes
 * white with nothing on screen and nothing to act on - the failure mode is
 * indistinguishable from a blank deploy. Showing the message costs nothing
 * and turns "it broke" into something reportable.
 *
 * Class component because error boundaries have no hooks equivalent; this is
 * the one place React still requires one.
 */
export default class ErrorBoundary extends Component {
  state = { error: null, info: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // Also goes to the console, so a report can be copied from DevTools.
    console.error('Spendline crashed:', error, info?.componentStack)
    this.setState({ info })
  }

  render() {
    const { error, info } = this.state
    if (!error) return this.props.children

    return (
      <div className="app">
        <div className="card crash-card">
          <h2>Something broke on this page</h2>
          <p className="card-subtitle">
            This is a bug in the app, not something you did. The details below
            identify it.
          </p>
          <pre className="code-block crash-detail">
            {String(error?.stack || error)}
            {info?.componentStack ? `\n\nComponent stack:${info.componentStack}` : ''}
          </pre>
          <div className="crash-actions">
            <button className="btn" onClick={() => window.location.reload()}>
              Reload
            </button>
            {/* A crash in the signed-in view usually can't be escaped by
                reloading, since the session restores and it happens again.
                Clearing local state gets back to a working page. */}
            <button
              className="btn secondary"
              onClick={() => {
                try { localStorage.clear() } catch { /* not available */ }
                window.location.replace('/')
              }}
            >
              Sign out and reset
            </button>
          </div>
        </div>
      </div>
    )
  }
}
