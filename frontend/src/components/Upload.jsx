import { useState, useRef } from 'react'
import { uploadCsv } from '../api'

/**
 * File upload component. Supports both click-to-pick and drag-and-drop.
 *
 * Calls onJobSubmitted(jobId) once the upload returns a job_id - the parent
 * is responsible for polling and showing results.
 */
// Served from the repo's /sample-data via Vite's publicDir.
const SAMPLE_URL = '/sample_transactions.csv'

export default function Upload({ onJobSubmitted, disabled }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setUploading(true)
    try {
      const result = await uploadCsv(file)
      onJobSubmitted(result.job_id)
    } catch (err) {
      // Backend returns structured errors via 400/413 etc; surface the detail.
      const detail = err.response?.data?.detail || err.message
      setError(detail)
    } finally {
      setUploading(false)
    }
  }

  // Runs the bundled sample through the same path a dropped file takes, so a
  // reviewer can see real results without needing a bank export of their own.
  const handleSample = async () => {
    if (disabled || uploading) return
    setError(null)
    try {
      const response = await fetch(SAMPLE_URL)
      if (!response.ok) throw new Error(`Sample data unavailable (${response.status})`)
      const blob = await response.blob()
      await handleFile(new File([blob], 'sample_transactions.csv', { type: 'text/csv' }))
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (disabled || uploading) return
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="card upload-card">
      <h2>Upload transactions</h2>
      <p className="card-subtitle">
        CSV with columns: date, category, amount (description optional)
      </p>

      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onClick={() => !disabled && !uploading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => handleFile(e.target.files[0])}
          disabled={disabled || uploading}
        />
        {uploading ? (
          <p><span className="spinner" /> Uploading...</p>
        ) : (
          <>
            <p><strong>Drop a CSV here</strong> or click to browse</p>
            <p className="hint">Maximum 10MB</p>
          </>
        )}
      </div>

      <p className="upload-sample">
        No export handy?{' '}
        <button type="button" className="link-btn" onClick={handleSample} disabled={disabled || uploading}>
          Try it with sample data
        </button>
        {' · '}
        <a href={SAMPLE_URL} download>Download the CSV</a>
      </p>

      {error && (
        <div className="status-banner error" style={{ marginTop: '1rem' }}>
          {error}
        </div>
      )}
    </div>
  )
}