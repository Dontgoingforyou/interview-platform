import { describe, expect, it } from 'vitest'

import {
  SAD_INTERN_METRICS_MAIN,
  SAD_INTERN_METRIC_TOOLTIP_KEYS,
} from '../../constants/sadInternMetrics'

describe('sadInternMetrics', () => {
  it('для каждой основной метрики задан ключ подсказки', () => {
    for (const m of SAD_INTERN_METRICS_MAIN) {
      expect(SAD_INTERN_METRIC_TOOLTIP_KEYS[m.key]).toBeDefined()
    }
  })
})
