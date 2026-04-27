import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxies /api → FastAPI backend during dev so the frontend doesn't need
// to know the backend URL (and avoids any CORS surprises in local dev).
//
// `server.watch.ignored` is needed because the project lives inside iCloud
// Drive, which periodically rewrites file metadata (atime/mtime) on
// vite.config.js and .env.local without changing their bytes. Chokidar
// reads that as a "change" → Vite restarts → strict-port rebind fails →
// browser 504s. Ignoring those two files breaks the loop while still
// hot-reloading every source file.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    watch: {
      ignored: [
        '**/vite.config.js',
        '**/.env',
        '**/.env.*',
      ],
    },
  },
})
