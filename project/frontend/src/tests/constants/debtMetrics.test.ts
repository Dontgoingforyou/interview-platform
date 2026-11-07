import { describe, expect, it } from 'vitest'

import { DEBT_METRICS_MAIN, DEBT_METRIC_TOOLTIP_KEYS } from '../../constants/debtMetrics'

describe('debtMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of DEBT_METRICS_MAIN) {
      expect(DEBT_METRIC_TOOLTIP_KEYS[String(m.key)]).toBeDefined()
    }
  })

  it('currency-метрики помечены format currency', () => {
    const currency = DEBT_METRICS_MAIN.filter((m) => m.format === 'currency')
    expect(currency.length).toBeGreaterThan(0)
    expect(currency.some((m) => m.key === 'sum-total')).toBe(true)
  })
})
