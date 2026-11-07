import type { DebtAnalytics } from '../../types/debt'

export function formatMetricCurrencyRub(value: number): string {
  const n = Math.trunc(Number(value))
  if (!Number.isFinite(n)) {
    return '—'
  }
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  const withSpaces = String(abs).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  return `${sign}${withSpaces} ₽`
}

export function numericDebtMetricValue(
  raw: DebtAnalytics,
  key: string,
  format?: 'percent' | 'currency',
): number | null {
  const v = raw[key as keyof DebtAnalytics]
  if (typeof v !== 'number' || !Number.isFinite(v) || v < 0) {
    return null
  }
  if (format === 'currency') {
    return Math.trunc(v)
  }
  return v
}

export function formatDebtMetricValue(
  raw: DebtAnalytics,
  key: string,
  format?: 'percent' | 'currency',
): string {
  const v = raw[key as keyof DebtAnalytics]
  if (v === undefined || v === null) {
    return '—'
  }
  if (format === 'percent' && typeof v === 'number') {
    return `${v.toFixed(1)}%`
  }
  if (format === 'currency' && typeof v === 'number') {
    return formatMetricCurrencyRub(v)
  }
  if (typeof v === 'number' && !Number.isInteger(v)) {
    return v.toFixed(2)
  }
  return String(v)
}
