import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxies /api → FastAPI backend during dev so the frontend doesn't need
// to know the backend URL (and avoids any CORS surprises in local dev).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
