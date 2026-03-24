import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api/auth': {
        target: 'http://auth-service:8001',
        rewrite: path => path.replace(/^\/api\/auth/, ''),
        changeOrigin: true,
      },
      '/api/tournaments': {
        target: 'http://tournament-service:8002',
        rewrite: path => path.replace(/^\/api\/tournaments/, '/tournaments'),
        changeOrigin: true,
      },
      '/api/matches': {
        target: 'http://match-service:8003',
        rewrite: path => path.replace(/^\/api\/matches/, '/matches'),
        changeOrigin: true,
      },
      '/api/stats': {
        target: 'http://stats-service:8004',
        rewrite: path => path.replace(/^\/api\/stats/, '/stats'),
        changeOrigin: true,
      },
    },
  },
})
