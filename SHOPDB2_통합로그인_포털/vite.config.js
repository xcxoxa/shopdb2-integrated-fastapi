import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8001'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 4173,
      strictPort: true,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          secure: false,
        },
        '/health': {
          target,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    preview: {
      host: '0.0.0.0',
      port: 4173,
      strictPort: true,
      proxy: {
        '/api': { target, changeOrigin: true, secure: false },
        '/health': { target, changeOrigin: true, secure: false },
      },
    },
  }
})
