import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite handles the dev server and the production build (which outputs static
// files into ./dist that nginx then serves). No SSR, no fancy stuff - we want
// the frontend to be a fully static artifact for portability.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
})