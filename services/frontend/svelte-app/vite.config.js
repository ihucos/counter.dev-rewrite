import { defineConfig, loadEnv } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env vars for the current mode
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [svelte()],
    resolve: {
      alias: {
        $lib: path.resolve('./src/lib'),
      },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
