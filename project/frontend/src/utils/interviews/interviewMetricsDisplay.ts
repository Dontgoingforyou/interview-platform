import type { InterviewAnalytics } from '../../types/interview'

/** Значение для count-up: только неотрицательные числа. */
export function numericMetricValue(
  raw: InterviewAnalytics,
  key: keyof InterviewAnalytics | string,
): number | null {
  const v = raw[key as keyof InterviewAnalytics]
  if (typeof v !== 'number' || !Number.isFinite(v) || v < 0) {
    return null
  }
  return v
}

export function formatMetricValue(
  raw: InterviewAnalytics,
  key: string,
  format?: 'percent' | 'decimal2',
): string {
  const v = raw[key as keyof InterviewAnalytics]
  if (v === undefined || v === null) {
    return '—'
  }
  if (format === 'percent' && typeof v === 'number') {
    return `${v.toFixed(1)}%`
  }
  if (format === 'decimal2' && typeof v === 'number') {
    return v.toFixed(2)
  }
  if (typeof v === 'number' && !Number.isInteger(v)) {
    return v.toFixed(2)
  }
  return String(v)
}

export function deepgramBalanceLabel(
  data: { amount?: number | null; error?: string } | undefined,
  isLoading: boolean,
): { text: string; isError: boolean } {
  if (isLoading) {
    return { text: 'Deepgram: …', isError: false }
  }
  if (data?.error) {
    return { text: 'Deepgram: н/д', isError: true }
  }
  if (data?.amount != null && Number.isFinite(Number(data.amount))) {
    return { text: `Deepgram: $${Number(data.amount).toFixed(2)}`, isError: false }
  }
  return { text: 'Deepgram: —', isError: false }
}
