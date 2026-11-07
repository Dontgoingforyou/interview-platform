import type { InterviewAnalytics } from '../types/interview'

export interface MetricMainConfig {
  key: keyof InterviewAnalytics | string
  label: string
  format?: 'percent' | 'decimal2'
  light?: boolean
  subtitleKey?: keyof InterviewAnalytics
}

export interface MetricAllTimeConfig {
  dataKey: keyof InterviewAnalytics
  label: string
  format?: 'percent' | 'decimal2'
  light?: boolean
  subtitleKey?: keyof InterviewAnalytics
}

export const METRICS_MAIN: MetricMainConfig[] = [
  { key: 'total', label: 'Всего собеседований' },
  { key: 'companies', label: 'Компаний в воронке' },
  { key: 'upcoming', label: 'Предстоящие интервью' },
  { key: 'this-week', label: 'На этой неделе' },
  { key: 'last-week', label: 'За последние 7 дней' },
  { key: 'success_rate', label: 'Доля успешных', format: 'percent' },
  { key: 'cancelled', label: 'Отмен/не состоялось' },
  {
    key: 'fastest_manager',
    label: 'Самый быстрый менеджер',
    light: true,
    subtitleKey: 'fastest_manager_count',
  },
  { key: 'avg_per_person', label: 'Интервью на кандидата', format: 'decimal2' },
  { key: 'avg_per_manager', label: 'Интервью на менеджера', format: 'decimal2' },
]

export const METRICS_ALL_TIME: MetricAllTimeConfig[] = [
  { dataKey: 'total_all_time', label: 'Всего собеседований' },
  { dataKey: 'companies_all_time', label: 'Компаний в воронке' },
  { dataKey: 'success_rate_all_time', label: 'Доля успешных', format: 'percent' },
  { dataKey: 'cancelled_all_time', label: 'Отмен/не состоялось' },
  {
    dataKey: 'top_manager_all_time',
    label: 'Самый активный менеджер',
    light: true,
    subtitleKey: 'top_manager_count_all_time',
  },
  { dataKey: 'avg_per_person_all_time', label: 'Интервью на кандидата', format: 'decimal2' },
  { dataKey: 'avg_per_manager_all_time', label: 'Интервью на менеджера', format: 'decimal2' },
]

/** Ключи `tooltips` из GET /api/analytics/interviews/ */
export const MAIN_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  total: 'total',
  companies: 'companies',
  upcoming: 'upcoming',
  'this-week': 'this-week',
  'last-week': 'last-week',
  success_rate: 'success-rate',
  cancelled: 'cancelled',
  fastest_manager: 'fastest-manager',
  avg_per_person: 'avg-per-person',
  avg_per_manager: 'avg-per-manager',
}

export const ALL_TIME_TOOLTIP_KEYS: Partial<Record<keyof InterviewAnalytics, string>> = {
  total_all_time: 'total-all-time',
  companies_all_time: 'companies-all-time',
  success_rate_all_time: 'success-rate-all-time',
  cancelled_all_time: 'cancelled-all-time',
  top_manager_all_time: 'top-manager-all-time',
  avg_per_person_all_time: 'avg-per-person-all-time',
  avg_per_manager_all_time: 'avg-per-manager-all-time',
}
