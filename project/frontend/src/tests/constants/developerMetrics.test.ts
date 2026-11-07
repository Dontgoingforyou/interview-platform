import { describe, expect, it } from 'vitest'

import {
  DEVELOPER_METRICS_MAIN,
  DEVELOPER_METRIC_TOOLTIP_KEYS,
} from '../../constants/developerMetrics'

describe('developerMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of DEVELOPER_METRICS_MAIN) {
      expect(DEVELOPER_METRIC_TOOLTIP_KEYS[m.key]).toBeDefined()
    }
  })

  it('средний оффер — currency', () => {
    const avg = DEVELOPER_METRICS_MAIN.find((m) => m.key === 'avg-offer-last-month')
    expect(avg?.format).toBe('currency')
  })
})
