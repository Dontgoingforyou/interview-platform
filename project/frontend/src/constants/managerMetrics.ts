import type { ManagersAnalytics } from '../types/managerDashboard'

export interface ManagerMetricConfig {
  key: keyof ManagersAnalytics | string
  label: string
  format?: 'decimal2'
  light?: boolean
  subtitleKey?: keyof ManagersAnalytics
  subtitleTemplate?: 'interviewsPeriod'
}

export const MANAGER_METRICS_MAIN: ManagerMetricConfig[] = [
  { key: 'managers', label: 'Менеджеров в работе' },
  { key: 'hot-candidates', label: 'Горячие (7 дн.)' },
  { key: 'active-candidates', label: 'В работе (20 дн.)' },
  { key: 'portfolio-candidates', label: 'В портфеле (60 дн.)' },
  { key: 'avg-candidates', label: 'Среднее собесов/менеджер', format: 'decimal2' },
  {
    key: 'top-speed',
    label: 'Самый быстрый менеджер',
    light: true,
    subtitleKey: 'top-speed-count',
    subtitleTemplate: 'interviewsPeriod',
  },
  { key: 'this-week', label: 'Интервью на этой неделе' },
]

/** Ключи подсказок совпадают с ключами метрик в API */
export const MANAGER_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  managers: 'managers',
  'hot-candidates': 'hot-candidates',
  'active-candidates': 'active-candidates',
  'portfolio-candidates': 'portfolio-candidates',
  'avg-candidates': 'avg-candidates',
  'top-speed': 'top-speed',
  'this-week': 'this-week',
}
