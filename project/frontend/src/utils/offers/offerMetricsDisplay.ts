import { formatMetricCurrencyRub } from '../debts/debtMetricsDisplay'
import type { OfferAnalytics } from '../../types/offer'

export function numericOfferMetricValue(
  raw: OfferAnalytics,
  key: string,
  format?: 'currency' | 'text',
): number | null {
  const v = raw[key as keyof OfferAnalytics]
  if (format === 'currency' && typeof v === 'number' && Number.isFinite(v) && v >= 0) {
    return Math.trunc(v)
  }
  return null
}

export function formatOfferMetricValue(
  raw: OfferAnalytics,
  key: string,
  format?: 'currency' | 'text',
): string {
  const v = raw[key as keyof OfferAnalytics]
  if (v === undefined || v === null) {
    return '—'
  }
  if (format === 'currency' && typeof v === 'number') {
    return formatMetricCurrencyRub(v)
  }
  return String(v)
}
