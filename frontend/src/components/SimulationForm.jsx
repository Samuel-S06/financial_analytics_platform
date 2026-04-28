import { useState } from 'react'
import { submitSimulation } from '../api'

/**
 * Form for submitting a simulation against a completed analysis.
 *
 * Categories come from the parent (extracted from the analysis result), so
 * the user only sees categories that actually exist in their data.
 *
 * Calls onJobSubmitted(jobId) once the simulate request is accepted.
 */
export default function SimulationForm({ analysisJobId, categories, onJobSubmitted }) {
  const [goalAmount, setGoalAmount] = useState(1000)
  const [months, setMonths] = useState(12)
  const [selected, setSelected] = useState(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const toggle = (cat) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const handleSubmit = async () => {
    setError(null)
    if (selected.size === 0) {
      setError('Pick at least one category to cut from')
      return
    }
    setSubmitting(true)
    try {
      const result = await submitSimulation({
        analysis_job_id: analysisJobId,
        goal_amount: Number(goalAmount),
        months: Number(months),
        cut_categories: Array.from(selected),
      })
      onJobSubmitted(result.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <h2>Simulate a savings goal</h2>
      <p className="card-subtitle">
        We'll calculate how much to cut from each selected category
      </p>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="goal">Goal amount ($)</label>
          <input
            id="goal"
            type="number"
            min="1"
            value={goalAmount}
            onChange={(e) => setGoalAmount(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="months">Over how many months?</label>
          <input
            id="months"
            type="number"
            min="1"
            max="120"
            value={months}
            onChange={(e) => setMonths(e.target.value)}
          />
        </div>
      </div>

      <div className="form-field" style={{ marginBottom: '1rem' }}>
        <label>Cut from these categories:</label>
        <div className="category-grid">
          {categories.map((cat) => (
            <label
              key={cat}
              className={`category-checkbox ${selected.has(cat) ? 'checked' : ''}`}
            >
              <input
                type="checkbox"
                checked={selected.has(cat)}
                onChange={() => toggle(cat)}
              />
              {cat}
            </label>
          ))}
        </div>
      </div>

      {error && (
        <div className="status-banner error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <button className="btn" onClick={handleSubmit} disabled={submitting}>
        {submitting ? <><span className="spinner" /> Submitting...</> : 'Run simulation'}
      </button>
    </div>
  )
}