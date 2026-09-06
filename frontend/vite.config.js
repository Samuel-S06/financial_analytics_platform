import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite handles the dev server and the production build (which outputs static
// files into ./dist that nginx then serves). No SSR, no fancy stuff - we want
// the frontend to be a fully static artifact for portability.
export default defineConfig({
  plugins: [react()],
  // Serve the repo's sample data as static assets, so /sample-data has one
  // home: discoverable at the repo root and downloadable from the running
  // app, with no second copy to drift out of sync. Its contents land at the
  // site root, so the CSV is served from /sample_transactions.csv.
  publicDir: fileURLToPath(new URL('../sample-data', import.meta.url)),
  build: {
    outDir: 'dist',
  },
  server: {
    port: 5173,
    // Mirror what nginx does in the container: forward /api/* to the backend
    // and strip the /api prefix, because FastAPI routes are /health, /upload,
    // etc. Without this, `npm run dev` has nothing serving /api and every
    // call 404s. Same-origin in dev means no CORS preflight either.
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
