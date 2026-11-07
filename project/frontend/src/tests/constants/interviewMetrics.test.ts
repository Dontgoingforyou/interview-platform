import { describe, expect, it } from 'vitest'

import { MAIN_METRIC_TOOLTIP_KEYS, METRICS_MAIN } from '../../constants/interviewMetrics'

describe('interviewMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of METRICS_MAIN) {
      expect(MAIN_METRIC_TOOLTIP_KEYS[String(m.key)]).toBeDefined()
    }
  })
})
