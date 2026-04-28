import axios from 'axios'

// All backend calls go through /api/* - nginx (in the frontend container)
// proxies these to the backend service. This means the frontend never needs
// to know the backend URL; it just talks to the same origin it was served
// from. Works identically in docker and k8s.
const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export const getHello = () => client.get('/hello').then(r => r.data)
export const getHealth = () => client.get('/health').then(r => r.data)