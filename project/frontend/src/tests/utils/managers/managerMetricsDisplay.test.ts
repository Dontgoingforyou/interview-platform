import { describe, expect, it } from 'vitest'

import type { ManagersAnalytics } from '../../../types/managerDashboard'
import {
  formatManagerMetricValue,
  numericManagerMetricValue,
} from '../../../utils/managers/managerMetricsDisplay'

describe('managerMetricsDisplay', () => {
  const raw = {
    managers: 4,
    'avg-candidates': 1.256,
    'top-speed': 'Иван',
  } as ManagersAnalytics

  it('format decimal2 / integer / string / —', () => {
    expect(formatManagerMetricValue(raw, 'avg-candidates', 'decimal2')).toBe('1.26')
    expect(formatManagerMetricValue(raw, 'avg-candidates')).toBe('1.26')
    expect(formatManagerMetricValue(raw, 'managers')).toBe('4')
    expect(formatManagerMetricValue(raw, 'top-speed')).toBe('Иван')
    expect(formatManagerMetricValue(raw, 'missing')).toBe('—')
  })

  it('numeric: decimal2 / integer / null', () => {
    expect(numericManagerMetricValue(raw, 'avg-candidates', 'decimal2')).toBe(1.256)
    expect(numericManagerMetricValue(raw, 'managers')).toBe(4)
    expect(numericManagerMetricValue(raw, 'avg-candidates')).toBeNull()
    expect(numericManagerMetricValue(raw, 'top-speed')).toBeNull()
  })
})
