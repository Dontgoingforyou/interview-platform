/** Карточки метрик на странице «Собесы (метрики)» / направления. */
export interface DirectionMetricCardConfig {
  /** Ключ для tooltips и data-metric */
  metricKey: string
  /** Поле в ответе API со значением */
  dataKey: string
  label: string
  subtitleDataKey?: string
  format?: 'percent'
}

export const DIRECTION_METRICS_MAIN: DirectionMetricCardConfig[] = [
  { metricKey: 'total-directions', dataKey: 'total-directions', label: 'Всего направлений' },
  { metricKey: 'directions', dataKey: 'directions', label: 'Направлений в работе' },
  {
    metricKey: 'top-direction',
    dataKey: 'top_direction_30',
    label: 'Самое активное направление',
  },
  {
    metricKey: 'best-conversion',
    dataKey: 'best_conversion',
    label: 'Лидеры по конверсии',
  },
  {
    metricKey: 'worst-conversion',
    dataKey: 'worst_conversion',
    label: 'Нуждаются в поддержке',
  },
  {
    metricKey: 'fastest',
    dataKey: 'fastest_direction',
    label: 'Самое быстрое направление',
    subtitleDataKey: 'fastest_direction_person',
  },
  {
    metricKey: 'slowest',
    dataKey: 'slowest_direction',
    label: 'Самое медленное направление',
    subtitleDataKey: 'slowest_direction_person',
  },
  {
    metricKey: 'best-month',
    dataKey: 'best_month',
    label: 'Лучший месяц',
  },
  {
    metricKey: 'worst-month',
    dataKey: 'worst_month',
    label: 'Минимум активности',
  },
  {
    metricKey: 'tech-share',
    dataKey: 'tech_share',
    label: 'Технических собеседований',
    format: 'percent',
  },
]

/** Ключ подсказки в объекте tooltips ответа API. */
export const DIRECTION_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  'total-directions': 'total-directions',
  directions: 'directions',
  'top-direction': 'top-direction',
  'best-conversion': 'best-conversion',
  'worst-conversion': 'worst-conversion',
  fastest: 'fastest',
  slowest: 'slowest',
  'best-month': 'best-month',
  'worst-month': 'worst-month',
  'tech-share': 'tech-share',
}
