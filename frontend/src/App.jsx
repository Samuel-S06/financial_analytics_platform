import { useState, useEffect } from 'react'
import { getHello } from './api'

// Spine-first stub: hits /api/hello and shows which backend pod responded.
// Hitting "Refresh" repeatedly is the demo for k8s service load-balancing -
// pod_hostname will rotate as the Service distributes requests across replicas.
//
// The real components (Upload, SimulationForm, ResultsChart) live under
// ./components/ and will be wired in once the spine is verified end-to-end.
function App() {
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchHello = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getHello()
      setResponse(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHello()
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 600, margin: '4rem auto', padding: '0 1rem' }}>
      <h1>Financial Analytics Platform</h1>
      <p style={{ color: '#666' }}>Spine check - this confirms the frontend can reach the backend through the ingress.</p>

      <button onClick={fetchHello} disabled={loading} style={{ padding: '0.5rem 1rem', fontSize: '1rem' }}>
        {loading ? 'Loading...' : 'Refresh'}
      </button>

      {error && (
        <pre style={{ background: '#fee', padding: '1rem', marginTop: '1rem' }}>
          Error: {error}
        </pre>
      )}

      {response && (
        <pre style={{ background: '#f4f4f4', padding: '1rem', marginTop: '1rem' }}>
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
    </div>
  )
}

export default App