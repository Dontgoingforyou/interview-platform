import { describe, expect, it } from 'vitest'

import type { DebtAnalytics } from '../../types/debt'
import {
  formatDebtMetricValue,
  formatMetricCurrencyRub,
  numericDebtMetricValue,
} from '../../utils/debts/debtMetricsDisplay'

describe('formatMetricCurrencyRub', () => {
  it.each([
    [1000, '1 000 ₽'],
    [50000, '50 000 ₽'],
    [0, '0 ₽'],
    [1234567, '1 234 567 ₽'],
  ])('%s → %s', (value, expected) => {
    expect(formatMetricCurrencyRub(value)).toBe(expected)
  })
})

describe('formatDebtMetricValue', () => {
  const base: Partial<DebtAnalytics> = {}

  it('currency как целые рубли с ₽', () => {
    const raw = { ...base, 'sum-total': 258661843.12 } as DebtAnalytics
    expect(formatDebtMetricValue(raw, 'sum-total', 'currency')).toBe('258 661 843 ₽')
  })

  it('percent один знак', () => {
    const raw = { ...base, 'avg-progress': 12.34 } as DebtAnalytics
    expect(formatDebtMetricValue(raw, 'avg-progress', 'percent')).toBe('12.3%')
  })
})

describe('numericDebtMetricValue', () => {
  it('для currency возвращает целую часть', () => {
    const raw = { 'sum-total': 99.9 } as DebtAnalytics
    expect(numericDebtMetricValue(raw, 'sum-total', 'currency')).toBe(99)
  })

  it('без формата — исходное число', () => {
    const raw = { total: 42.7 } as DebtAnalytics
    expect(numericDebtMetricValue(raw, 'total')).toBe(42.7)
  })
})
