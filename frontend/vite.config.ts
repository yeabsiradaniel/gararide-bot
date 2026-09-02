import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' so the built assets load correctly when FastAPI serves them as static
// files under the Mini App URL.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist' },
  server: { port: 5173 },
})
