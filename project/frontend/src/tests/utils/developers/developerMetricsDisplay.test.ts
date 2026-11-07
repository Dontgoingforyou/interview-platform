import { describe, expect, it } from 'vitest'

import type { DeveloperAnalytics } from '../../../types/developer'
import {
  formatDeveloperMetricValue,
  numericDeveloperMetricValue,
} from '../../../utils/developers/developerMetricsDisplay'

describe('developerMetricsDisplay', () => {
  const raw = {
    'active-specialists': 10,
    'avg-offer-last-month': 150000.9,
  } as DeveloperAnalytics

  it('numeric только для currency >= 0', () => {
    expect(numericDeveloperMetricValue(raw, 'avg-offer-last-month', 'currency')).toBe(150000)
    expect(numericDeveloperMetricValue(raw, 'active-specialists')).toBeNull()
    expect(numericDeveloperMetricValue(raw, 'active-specialists', 'currency')).toBe(10)
  })

  it('format: currency / string / —', () => {
    expect(formatDeveloperMetricValue(raw, 'avg-offer-last-month', 'currency')).toContain('₽')
    expect(formatDeveloperMetricValue(raw, 'active-specialists')).toBe('10')
    expect(formatDeveloperMetricValue({} as DeveloperAnalytics, 'x')).toBe('—')
  })
})
