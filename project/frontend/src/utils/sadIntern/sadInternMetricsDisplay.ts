import type { SadInternAnalytics } from '../../types/sadIntern'

export function formatSadInternMetricDisplay(
  analytics: SadInternAnalytics,
  key: string,
  format: 'integer' | 'days',
): string {
  if (key === 'total') {
    return String(analytics.total)
  }
  if (key === 'with_contact') {
    return String(analytics.with_contact)
  }
  if (key === 'avg_wait') {
    return String(Math.round(Number(analytics.avg_wait)))
  }
  if (key === 'longest_wait_days') {
    return String(analytics.longest_wait_days)
  }
  if (format === 'days') {
    return String(analytics.longest_wait_days)
  }
  return '0'
}

export function numericSadInternMetric(analytics: SadInternAnalytics, key: string): number {
  if (key === 'total') {
    return analytics.total
  }
  if (key === 'with_contact') {
    return analytics.with_contact
  }
  if (key === 'avg_wait') {
    return Number(analytics.avg_wait)
  }
  if (key === 'longest_wait_days') {
    return analytics.longest_wait_days
  }
  return 0
}
