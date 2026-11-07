/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// vite.config.ts — аналог settings.py для фронтенда.
// defineConfig — функция-обёртка для автодополнения TypeScript.
export default defineConfig(({ command }) => ({
  // В production base должен совпадать с STATIC_URL + static_url_prefix (django-vite):
  // '/static/frontend/' — иначе chunk-и уйдут в /assets/... и nginx их не отдаст.
  // В dev — '/' чтобы SPA и OAuth callback открывались с http://localhost:5173/... без префикса.
  base: command === 'build' ? '/static/frontend/' : '/',

  plugins: [
    react(),
  ],

  server: {
    // Django будет работать на стандартном 8000, Vite — на 5173.
    port: 5173,

    // Аналог nginx-прокси: запрос /api/interviews/ → Django 8000/api/interviews/
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Долгие multipart (видео до 10 ГБ); иначе по умолчанию ~2 мин proxyTimeout — обрыв при dev.
        proxyTimeout: 7_200_000,
        timeout: 7_200_000,
      },
      '/accounts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: '../staticfiles/frontend',
    emptyOutDir: true,
    manifest: true,
  },

  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    include: ['src/tests/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary'],
      include: ['src/utils/**/*.{ts,tsx}', 'src/constants/**/*.{ts,tsx}'],
      exclude: [
        'src/tests/**',
        'src/**/*.d.ts',
        'src/**/*.test.ts',
        'src/**/*.test.tsx',
      ],
      thresholds: {
        lines: 90,
      },
    },
  },
}))
