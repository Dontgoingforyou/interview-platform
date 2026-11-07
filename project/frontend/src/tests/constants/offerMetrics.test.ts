import { describe, expect, it } from 'vitest'

import { OFFER_METRICS_MAIN, OFFER_METRIC_TOOLTIP_KEYS } from '../../constants/offerMetrics'

describe('offerMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of OFFER_METRICS_MAIN) {
      expect(OFFER_METRIC_TOOLTIP_KEYS[String(m.key)]).toBeDefined()
    }
  })

  it('текстовые метрики помечены format text', () => {
    const text = OFFER_METRICS_MAIN.filter((m) => m.format === 'text')
    expect(text.some((m) => m.key === 'popular-company')).toBe(true)
  })
})
