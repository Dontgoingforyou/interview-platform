/** Карточки метрик на странице «Разработчики (период)». */
export interface DeveloperMetricConfig {
  key: string
  label: string
  format?: 'currency'
  light?: boolean
  subtitleKey?: string
  subtitleSuffix?: string
}

export const DEVELOPER_METRICS_MAIN: DeveloperMetricConfig[] = [
  { key: 'active-specialists', label: 'Всего специалистов' },
  { key: 'offers-this-year', label: 'Получили офферы' },
  { key: 'avg-offer-last-month', label: 'Средний оффер', format: 'currency' },
  {
    key: 'fastest-direction',
    label: 'Топ направление по скорости',
    light: true,
    subtitleKey: 'fastest-direction-days',
    subtitleSuffix: ' дн.',
  },
  {
    key: 'top-direction-offers',
    label: 'Топ направлений по кол-ву офферов',
    light: true,
  },
]

/** Ключи tooltips в ответе API (совпадают с metric_key в legacy). */
export const DEVELOPER_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  'active-specialists': 'active-specialists',
  'offers-this-year': 'offers-this-year',
  'avg-offer-last-month': 'avg-offer-last-month',
  'fastest-direction': 'fastest-direction',
  'top-direction-offers': 'top-direction-offers',
}
