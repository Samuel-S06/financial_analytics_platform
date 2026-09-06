import { useState, useRef } from 'react'
import { uploadCsv } from '../api'

/**
 * File upload component. Supports both click-to-pick and drag-and-drop.
 *
 * Calls onJobSubmitted(jobId) once the upload returns a job_id - the parent
 * is responsible for polling and showing results.
 */
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

      {error && (
        <div className="status-banner error" style={{ marginTop: '1rem' }}>
          {error}
        </div>
      )}
    </div>
  )
}