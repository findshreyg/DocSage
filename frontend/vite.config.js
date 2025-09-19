// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true, // Exit if port 3000 is not available
    host: true, // Listen on all addresses
  },
})
