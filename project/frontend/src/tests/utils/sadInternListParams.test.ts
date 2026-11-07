import { describe, expect, it } from 'vitest'

import { buildSadInternGroupedParams } from '../../utils/sadIntern/sadInternListParams'

describe('buildSadInternGroupedParams', () => {
  const baseFilters = {
    order_by: 'days_waiting',
    order_dir: 'desc' as const,
    on_project_page: 1,
  }

  it('не дублирует префикс page_ для pagination_key с API (page_5)', () => {
    const p = buildSadInternGroupedParams(baseFilters, 0, { page_5: 2 })
    expect(p.page_5).toBe(2)
    expect((p as Record<string, unknown>).page_page_5).toBeUndefined()
  })

  it('добавляет префикс для ключа из URL (5 -> page_5)', () => {
    const p = buildSadInternGroupedParams(baseFilters, 0, { '5': 2 })
    expect(p.page_5).toBe(2)
  })

  it('поддерживает направление none', () => {
    const p = buildSadInternGroupedParams(baseFilters, 0, { page_none: 3 })
    expect(p.page_none).toBe(3)
  })
})
