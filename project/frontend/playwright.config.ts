import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig, devices } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * E2E: Vite dev и VITE_DEV_BYPASS_AUTH.
 *
 * Данные в таблицах и метриках приходят с Django (`/api` → proxy на :8000 в vite.config.ts).
 * Без бэкенда возможны InlineError — смоки проверяют навигацию и ключевой UI.
 */
export default defineConfig({
  testDir: path.join(__dirname, 'e2e'),
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
  webServer: {
    // Сборка портала использует base '/static/frontend/'. Смокам нужен корень, как у страницы /login.
    command:
      'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort --base /',
    cwd: __dirname,
    url: 'http://127.0.0.1:5173/',
    reuseExistingServer: !process.env.CI,
    env: {
      ...process.env,
      NODE_ENV: 'development',
      VITE_DEV_BYPASS_AUTH: 'true',
      VITE_DEV_MOCK_ROLE: 'manager',
    },
  },
})
