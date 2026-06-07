import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': {
        // Point this to your Django backend
        // Common ports: 8000 (Django dev), 80, 8080
        target: process.env.API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
