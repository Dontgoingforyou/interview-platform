import { describe, expect, it } from 'vitest'

import { MANAGER_METRICS_MAIN, MANAGER_METRIC_TOOLTIP_KEYS } from '../../constants/managerMetrics'

describe('managerMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of MANAGER_METRICS_MAIN) {
      expect(MANAGER_METRIC_TOOLTIP_KEYS[String(m.key)]).toBeDefined()
    }
  })

  it('avg-candidates — decimal2', () => {
    expect(MANAGER_METRICS_MAIN.find((m) => m.key === 'avg-candidates')?.format).toBe('decimal2')
  })
})
