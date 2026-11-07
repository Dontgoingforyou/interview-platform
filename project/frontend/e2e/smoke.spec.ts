import { test, expect } from '@playwright/test'

/**
 * Смоки ключевых маршрутов при dev-обходе SSO.
 * Селекторы — по ролям и стабильным заголовкам (см. docs/REACT_MIGRATION EPIC-19).
 */
test.describe('SPA smoke', () => {
  test('страница входа с обходом SSO перенаправляет на собеседования', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL(/\/interviews\/?$/)
    await expect(
      page.getByRole('heading', { name: /Общая аналитика собеседований/i }),
    ).toBeVisible({ timeout: 30_000 })
  })

  test('раздел сотрудников открывается и показывает вводную карточку', async ({ page }) => {
    await page.goto('/employees')
    await expect(page.getByRole('heading', { name: 'Менеджеры' })).toBeVisible({ timeout: 30_000 })
  })
})
