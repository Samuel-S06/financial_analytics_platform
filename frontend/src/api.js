import axios from 'axios'
import { supabase } from './lib/supabase'

// All backend calls go through /api/* - nginx (in the frontend container) or
// the Vite dev proxy forwards these to the backend. VITE_API_URL overrides the
// base for deployments where the frontend and API live on different hosts.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
})

// Attach the Supabase access token to every request. Reading the session per
// request (rather than caching the token) means a token refreshed in the
// background is picked up automatically.
client.interceptors.request.use(async (config) => {
  if (supabase) {
    const { data } = await supabase.auth.getSession()
    const token = data.session?.access_token
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
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

/** The signed-in user's own uploads, newest first. */
export const listJobs = () =>
  client.get('/jobs').then(r => r.data)

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

/** Live exchange rates for converting displayed totals. */
export const getRates = (base = 'USD') =>
  client.get('/rates', { params: { base } }).then(r => r.data)
