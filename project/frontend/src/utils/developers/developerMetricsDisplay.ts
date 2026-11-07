import { formatMetricCurrencyRub } from '../debts/debtMetricsDisplay'
import type { DeveloperAnalytics } from '../../types/developer'

export function numericDeveloperMetricValue(
  raw: DeveloperAnalytics,
  key: string,
  format?: 'currency',
): number | null {
  const v = raw[key as keyof DeveloperAnalytics]
  if (format === 'currency' && typeof v === 'number' && Number.isFinite(v) && v >= 0) {
    return Math.trunc(v)
  }
  return null
}

export function formatDeveloperMetricValue(
  raw: DeveloperAnalytics,
  key: string,
  format?: 'currency',
): string {
  const v = raw[key as keyof DeveloperAnalytics]
  if (v === undefined || v === null) {
    return '—'
  }
  if (format === 'currency' && typeof v === 'number') {
    return formatMetricCurrencyRub(v)
  }
  return String(v)
}
