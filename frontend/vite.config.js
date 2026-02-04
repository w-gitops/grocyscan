import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    vue({ template: { transformAssetUrls } }),
    quasar(),
  ],
  server: {
    port: 3335,
    proxy: {
      '/api': { target: 'http://localhost:3334', changeOrigin: true },
      '/health': { target: 'http://localhost:3334', changeOrigin: true },
    },
  },
})
