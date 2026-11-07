import { describe, expect, it } from 'vitest'

import type { SadInternAnalytics } from '../../../types/sadIntern'
import {
  formatSadInternMetricDisplay,
  numericSadInternMetric,
} from '../../../utils/sadIntern/sadInternMetricsDisplay'

const analytics: SadInternAnalytics = {
  total: 12,
  with_contact: 8,
  avg_wait: 15.6,
  longest_wait_days: 40,
  longest_wait_name: 'Иван',
  tooltips: {},
}

describe('sadInternMetricsDisplay', () => {
  it('format известных ключей и fallback', () => {
    expect(formatSadInternMetricDisplay(analytics, 'total', 'integer')).toBe('12')
    expect(formatSadInternMetricDisplay(analytics, 'with_contact', 'integer')).toBe('8')
    expect(formatSadInternMetricDisplay(analytics, 'avg_wait', 'days')).toBe('16')
    expect(formatSadInternMetricDisplay(analytics, 'longest_wait_days', 'days')).toBe('40')
    expect(formatSadInternMetricDisplay(analytics, 'unknown', 'days')).toBe('40')
    expect(formatSadInternMetricDisplay(analytics, 'unknown', 'integer')).toBe('0')
  })

  it('numeric ключей и 0 для неизвестного', () => {
    expect(numericSadInternMetric(analytics, 'total')).toBe(12)
    expect(numericSadInternMetric(analytics, 'with_contact')).toBe(8)
    expect(numericSadInternMetric(analytics, 'avg_wait')).toBe(15.6)
    expect(numericSadInternMetric(analytics, 'longest_wait_days')).toBe(40)
    expect(numericSadInternMetric(analytics, 'nope')).toBe(0)
  })
})
