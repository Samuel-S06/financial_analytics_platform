import { useEffect } from 'react'
import { pollJob } from '../api'

/**
 * Polls a job and calls onComplete with the final result, or onError on failure.
 * Renders a status banner while polling.
 *
 * Mounting/unmounting this component starts/stops polling - parent controls
 * the lifecycle by deciding when to render it.
 */
export default function JobStatus({ jobId, label, onComplete, onError }) {
  useEffect(() => {
    let cancelled = false

    pollJob(jobId)
      .then((job) => {
        if (cancelled) return
        if (job.status === 'done') {
          onComplete(job.result)
        } else {
          onError(job.error || 'Job failed')
        }
      })
      .catch((err) => {
        if (cancelled) return
        onError(err.message)
      })

    // If the parent unmounts us mid-poll (e.g. user navigates away), stop
    // pushing updates. The actual HTTP polling will run to completion but
    // its results get ignored.
    return () => { cancelled = true }
  }, [jobId, onComplete, onError])

  return (
    <div className="status-banner info">
      <span className="spinner" />
      <span>{label || 'Working...'} (job: <code>{jobId.slice(0, 8)}</code>)</span>
    </div>
  )
}