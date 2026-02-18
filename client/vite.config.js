import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true, // This allows the server to be exposed to the network
    allowedHosts: [
      'motoelectricacol.co',
      '.motoelectricacol.co' // The dot allows subdomains too
    ]
  }
})