import type { DebtAnalytics } from '../types/debt'

export interface DebtMetricConfig {
  key: keyof DebtAnalytics | string
  label: string
  format?: 'percent' | 'currency'
  light?: boolean
  subtitleKey?: keyof DebtAnalytics
}

export const DEBT_METRICS_MAIN: DebtMetricConfig[] = [
  { key: 'total', label: 'Всего людей в таблице' },
  { key: 'active', label: 'Активные должники' },
  { key: 'closed', label: 'Закрытых договоров' },
  { key: 'sum-total', label: 'Общая сумма договоров', format: 'currency' },
  { key: 'sum-paid', label: 'Выплачено по таблице', format: 'currency' },
  { key: 'sum-out', label: 'Остаток к получению', format: 'currency' },
  { key: 'avg-out', label: 'Средний остаток на активного', format: 'currency' },
  { key: 'avg-progress', label: 'Средний прогресс выплат', format: 'percent' },
  {
    key: 'top-out',
    label: 'Максимальный остаток',
    format: 'currency',
    light: true,
    subtitleKey: 'top-out-person',
  },
  { key: 'no-payments', label: 'Людей без платежей' },
]

/** Ключи tooltips из API (с дефисами) */
export const DEBT_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  total: 'total',
  active: 'active',
  closed: 'closed',
  'sum-total': 'sum-total',
  'sum-paid': 'sum-paid',
  'sum-out': 'sum-out',
  'avg-out': 'avg-out',
  'avg-progress': 'avg-progress',
  'top-out': 'top-out',
  'no-payments': 'no-payments',
}
