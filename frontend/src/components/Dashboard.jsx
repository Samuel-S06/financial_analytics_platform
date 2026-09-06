import { useCallback, useEffect, useState } from 'react'
import { listJobs } from '../api'
import { useAuth } from '../context/AuthContext'
import { useCurrency } from '../context/CurrencyContext'
import CurrencyPicker from './CurrencyPicker'
import DashboardHeader from './DashboardHeader'
import EmptyState from './EmptyState'
import JobStatus from './JobStatus'
import ResultsChart from './ResultsChart'
import SimulationForm from './SimulationForm'
import SimulationResults from './SimulationResults'
import Upload from './Upload'

/**
 * The signed-in view. State machine:
 *
 *   no upload      -> <Upload />
 *   upload pending -> <JobStatus /> for the upload
 *   upload done    -> <ResultsChart /> + <SimulationForm />
 *   sim pending    -> also <JobStatus /> for the simulation
 *   sim done       -> also <SimulationResults />
 *
 * All state lives here and the pieces below are stateless - no prop drilling,
 * no context.
 */
export default function Dashboard() {
  const { user, signOut } = useAuth()
  const { money, asOf, stale } = useCurrency()

  const [uploadJobId, setUploadJobId] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [analysisError, setAnalysisError] = useState(null)

  const [simJobId, setSimJobId] = useState(null)
  const [simResult, setSimResult] = useState(null)
  const [simError, setSimError] = useState(null)

  // The user's own upload history. Scoped server-side by the token, so this
  // never contains anyone else's jobs.
  const [history, setHistory] = useState([])
  // Tracked separately so the empty state doesn't flash before the first
  // response lands for someone who does have uploads.
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const refreshHistory = useCallback(() => {
    listJobs()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setHistoryLoaded(true))
  }, [])

  useEffect(() => { refreshHistory() }, [refreshHistory])
  // Re-fetch once an analysis lands, so the new upload shows up in the list.
  useEffect(() => { if (analysis) refreshHistory() }, [analysis, refreshHistory])

  const reset = () => {
    setUploadJobId(null)
    setAnalysis(null)
    setAnalysisError(null)
    setSimJobId(null)
    setSimResult(null)
    setSimError(null)
  }

  const handleSimulationSubmitted = (jobId) => {
    setSimResult(null)
    setSimError(null)
    setSimJobId(jobId)
  }

  return (
    <>
      <DashboardHeader
        email={user?.email}
        meta={asOf ? (stale ? 'rates may be out of date' : `rates ${asOf}`) : null}
        controls={<CurrencyPicker />}
        onSignOut={signOut}
      />

      {!uploadJobId && (
        <>
          <Upload onJobSubmitted={setUploadJobId} />
          {historyLoaded && history.length === 0 && <EmptyState />}
        </>
      )}

      {uploadJobId && !analysis && !analysisError && (
        <JobStatus
          jobId={uploadJobId}
          label="Analyzing your transactions"
          onComplete={setAnalysis}
          onError={setAnalysisError}
        />
      )}

      {analysisError && (
        <>
          <div className="status-banner error">Analysis failed: {analysisError}</div>
          <button className="btn secondary" onClick={reset}>Try again</button>
        </>
      )}

      {analysis && (
        <>
          <ResultsChart result={analysis} />

          <SimulationForm
            analysisJobId={uploadJobId}
            categories={analysis.by_category.map((c) => c.category)}
            onJobSubmitted={handleSimulationSubmitted}
          />

          {simJobId && !simResult && !simError && (
            <JobStatus
              jobId={simJobId}
              label="Running simulation"
              onComplete={setSimResult}
              onError={setSimError}
            />
          )}

          {simError && (
            <div className="status-banner error">Simulation failed: {simError}</div>
          )}

          {simResult && <SimulationResults result={simResult} />}

          <div style={{ marginTop: '1.5rem' }}>
            <button className="btn secondary" onClick={reset}>
              Start over with a new file
            </button>
          </div>
        </>
      )}

      {!analysis && history.length > 0 && (
        <div className="card">
          <h2>Your recent uploads</h2>
          <p className="card-subtitle">
            Only yours - the API scopes every job to the signed-in account.
          </p>
          <ul className="history-list">
            {history.map((job) => (
              <li key={job.job_id}>
                <span className="history-date">
                  {job.created_at
                    ? new Date(job.created_at * 1000).toLocaleString()
                    : '—'}
                </span>
                <span className="history-total">
                  {job.total_spend != null ? money(job.total_spend) : job.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <footer className="footer">
        <span>Made with love by Samuel Sosa © 2026</span>
        <a href="/api/health" target="_blank" rel="noopener">API status</a>
      </footer>
    </>
  )
}
