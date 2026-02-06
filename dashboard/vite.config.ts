import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',  // Served from root of FastAPI server
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,  // Disable for production
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ['recharts']
        }
      }
    },
    chunkSizeWarningLimit: 1000  // Increase limit for large chunks
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/override': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
