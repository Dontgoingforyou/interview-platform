import type { ManagersAnalytics } from '../../types/managerDashboard'

export function formatManagerMetricValue(
  raw: ManagersAnalytics,
  key: string,
  format?: 'decimal2',
): string {
  const v = (raw as unknown as Record<string, unknown>)[key]
  if (v === undefined || v === null) {
    return '—'
  }
  if (format === 'decimal2' && typeof v === 'number') {
    return v.toFixed(2)
  }
  if (typeof v === 'number' && !Number.isInteger(v)) {
    return v.toFixed(2)
  }
  return String(v)
}

export function numericManagerMetricValue(
  raw: ManagersAnalytics,
  key: string,
  format?: 'decimal2',
): number | null {
  const v = (raw as unknown as Record<string, unknown>)[key]
  if (typeof v !== 'number' || !Number.isFinite(v)) {
    return null
  }
  if (format === 'decimal2') {
    return v
  }
  if (Number.isInteger(v) && v >= 0) {
    return v
  }
  return null
}
