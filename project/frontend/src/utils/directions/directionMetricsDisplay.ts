import type { DirectionMetricsResponse } from '../../types/direction'

function rawValue(analytics: DirectionMetricsResponse, dataKey: string): unknown {
  if (dataKey === 'total-directions') {
    return analytics['total-directions']
  }
  return (analytics as unknown as Record<string, unknown>)[dataKey]
}

export function formatDirectionMetricValue(
  analytics: DirectionMetricsResponse,
  dataKey: string,
  format?: 'percent',
): string {
  const v = rawValue(analytics, dataKey)
  if (v === undefined || v === null || v === '') {
    return '—'
  }
  if (format === 'percent' && typeof v === 'number') {
    return `${v.toFixed(1)}%`
  }
  return String(v)
}

export function numericDirectionMetricValue(
  analytics: DirectionMetricsResponse,
  dataKey: string,
  format?: 'percent',
): number | null {
  const v = rawValue(analytics, dataKey)
  if (typeof v !== 'number' || !Number.isFinite(v) || v < 0) {
    return null
  }
  if (format === 'percent') {
    return v
  }
  if (dataKey === 'total-directions' || dataKey === 'directions') {
    return v
  }
  return null
}
