import { describe, expect, it } from 'vitest'

import type { DebtAnalytics } from '../../../types/debt'
import {
  formatDebtMetricValue,
  formatMetricCurrencyRub,
  numericDebtMetricValue,
} from '../../../utils/debts/debtMetricsDisplay'

describe('formatMetricCurrencyRub edges', () => {
  it('отрицательные и non-finite', () => {
    expect(formatMetricCurrencyRub(-1500)).toBe('-1 500 ₽')
    expect(formatMetricCurrencyRub(Number.NaN)).toBe('—')
  })
})

describe('numericDebtMetricValue edges', () => {
  it('null для не-числа и отрицательных', () => {
    expect(numericDebtMetricValue({ total: -1 } as DebtAnalytics, 'total')).toBeNull()
    expect(numericDebtMetricValue({} as DebtAnalytics, 'missing')).toBeNull()
  })
})

describe('formatDebtMetricValue edges', () => {
  it('— / decimal / string', () => {
    expect(formatDebtMetricValue({} as DebtAnalytics, 'total')).toBe('—')
    const raw = { total: 1.234 } as DebtAnalytics
    expect(formatDebtMetricValue(raw, 'total')).toBe('1.23')
    expect(formatDebtMetricValue({ total: 5 } as DebtAnalytics, 'total')).toBe('5')
  })
})
