import { describe, expect, it } from 'vitest'

import {
  DIRECTION_METRICS_MAIN,
  DIRECTION_METRIC_TOOLTIP_KEYS,
} from '../../constants/directionMetrics'

describe('directionMetrics', () => {
  it('для каждой карточки задан ключ подсказки', () => {
    for (const m of DIRECTION_METRICS_MAIN) {
      expect(DIRECTION_METRIC_TOOLTIP_KEYS[m.metricKey]).toBeDefined()
    }
  })

  it('tech-share — percent', () => {
    const tech = DIRECTION_METRICS_MAIN.find((m) => m.metricKey === 'tech-share')
    expect(tech?.format).toBe('percent')
    expect(tech?.dataKey).toBe('tech_share')
  })
})
