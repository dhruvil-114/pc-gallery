import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/thumbnail': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/image': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/person-face': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
