import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Send any request starting with /api to the FastAPI server.
    // The browser only ever talks to Vite, so no CORS setup is needed.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})