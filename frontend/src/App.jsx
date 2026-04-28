import { useState } from 'react'
import Upload from './components/Upload'
import JobStatus from './components/JobStatus'
import ResultsChart from './components/ResultsChart'
import SimulationForm from './components/SimulationForm'
import SimulationResults from './components/SimulationResults'

/**
 * Top-level state machine for the app:
 *
 *   no upload     -> show <Upload />
 *   upload pending -> show <JobStatus /> for the upload
 *   upload done    -> show <ResultsChart /> + <SimulationForm />
 *   sim pending    -> also show <JobStatus /> for the simulation
 *   sim done       -> also show <SimulationResults />
 *
 * Each piece is stateless and gets handlers from here. Keeping all the state
 * in one place makes the data flow obvious - no prop drilling, no context.
 */
export default function App() {
  // Upload / analysis lifecycle
  const [uploadJobId, setUploadJobId] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [analysisError, setAnalysisError] = useState(null)

  // Simulation lifecycle
  const [simJobId, setSimJobId] = useState(null)
  const [simResult, setSimResult] = useState(null)
  const [simError, setSimError] = useState(null)

  // "Start over" - resets everything to the empty state.
  const reset = () => {
    setUploadJobId(null)
    setAnalysis(null)
    setAnalysisError(null)
    setSimJobId(null)
    setSimResult(null)
    setSimError(null)
  }

  // Whenever the user submits a new simulation, clear the previous result so
  // the polling spinner shows clean.
  const handleSimulationSubmitted = (jobId) => {
    setSimResult(null)
    setSimError(null)
    setSimJobId(jobId)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Financial Analytics Platform</h1>
        <p className="subtitle">
          Upload transactions, see spending breakdowns, and simulate savings goals.
        </p>
      </header>

      {/* --- Upload flow --- */}
      {!uploadJobId && (
        <Upload onJobSubmitted={setUploadJobId} />
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
          <div className="status-banner error">
            Analysis failed: {analysisError}
          </div>
          <button className="btn secondary" onClick={reset}>Try again</button>
        </>
      )}

      {/* --- Analysis results --- */}
      {analysis && (
        <>
          <ResultsChart result={analysis} />

          <SimulationForm
            analysisJobId={uploadJobId}
            categories={analysis.by_category.map((c) => c.category)}
            onJobSubmitted={handleSimulationSubmitted}
          />

          {/* --- Simulation flow --- */}
          {simJobId && !simResult && !simError && (
            <JobStatus
              jobId={simJobId}
              label="Running simulation"
              onComplete={setSimResult}
              onError={setSimError}
            />
          )}

          {simError && (
            <div className="status-banner error">
              Simulation failed: {simError}
            </div>
          )}

          {simResult && <SimulationResults result={simResult} />}

          <div style={{ marginTop: '1.5rem' }}>
            <button className="btn secondary" onClick={reset}>
              Start over with a new file
            </button>
          </div>
        </>
      )}

      <footer className="footer">
        Deployed on Kubernetes · FastAPI + React · {' '}
        <a
          href="/api/health"
          target="_blank"
          rel="noopener"
          style={{ color: 'var(--accent)' }}
        >
          backend health
        </a>
      </footer>
    </div>
  )
}