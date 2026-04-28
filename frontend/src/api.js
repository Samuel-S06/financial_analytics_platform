import axios from 'axios'

// All backend calls go through /api/* - nginx (in the frontend container)
// proxies these to the backend service. The frontend never needs to know
// the backend URL; it just talks to the same origin it was served from.
const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// --- Endpoints ---

export const uploadCsv = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const getJob = (jobId) =>
  client.get(`/job/${jobId}`).then(r => r.data)

export const submitSimulation = (params) =>
  client.post('/simulate', params).then(r => r.data)

// Helper: poll a job until it's done or failed. Returns the final job record.
// Polls every `intervalMs` until the status is terminal.
export const pollJob = async (jobId, { intervalMs = 1000, maxAttempts = 60 } = {}) => {
  for (let i = 0; i < maxAttempts; i++) {
    const job = await getJob(jobId)
    if (job.status === 'done' || job.status === 'failed') {
      return job
    }
    // Wait before the next poll. Promise + setTimeout = the simplest async sleep.
    await new Promise(resolve => setTimeout(resolve, intervalMs))
  }
  throw new Error('Job polling timed out')
}