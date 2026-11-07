import { describe, expect, it } from 'vitest'

import type { DirectionMetricsResponse } from '../../../types/direction'
import {
  formatDirectionMetricValue,
  numericDirectionMetricValue,
} from '../../../utils/directions/directionMetricsDisplay'

describe('directionMetricsDisplay', () => {
  const analytics = {
    'total-directions': 5,
    directions: 3,
    tech_share: 0.42,
    top_direction_30: 'Java',
  } as unknown as DirectionMetricsResponse

  it('format percent / string / empty', () => {
    expect(formatDirectionMetricValue(analytics, 'tech_share', 'percent')).toBe('0.4%')
    expect(formatDirectionMetricValue(analytics, 'total-directions')).toBe('5')
    expect(formatDirectionMetricValue(analytics, 'missing')).toBe('—')
  })

  it('numeric: percent и счётчики направлений', () => {
    expect(numericDirectionMetricValue(analytics, 'tech_share', 'percent')).toBe(0.42)
    expect(numericDirectionMetricValue(analytics, 'total-directions')).toBe(5)
    expect(numericDirectionMetricValue(analytics, 'directions')).toBe(3)
    expect(numericDirectionMetricValue(analytics, 'top_direction_30')).toBeNull()
    expect(numericDirectionMetricValue(analytics, 'tech_share')).toBeNull()
  })
})
