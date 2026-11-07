import type { OfferAnalytics } from '../types/offer'

export interface OfferMetricConfig {
  key: keyof OfferAnalytics | string
  label: string
  format?: 'currency' | 'text'
  light?: boolean
}

export const OFFER_METRICS_MAIN: OfferMetricConfig[] = [
  { key: 'total', label: 'Всего офферов' },
  { key: 'directions', label: 'Уникальных направлений' },
  { key: 'companies', label: 'Компаний в списке' },
  { key: 'avg-offer', label: 'Средний оффер', format: 'currency' },
  { key: 'median-offer', label: 'Медианный оффер', format: 'currency' },
  { key: 'max-offer', label: 'Максимальный оффер', format: 'currency', light: true },
  { key: 'min-offer', label: 'Минимальный оффер', format: 'currency' },
  { key: 'popular-company', label: 'Самая популярная компания', format: 'text' },
  { key: 'best-company', label: 'Компания с высоким средним', format: 'text' },
  { key: 'best-month', label: 'Лучший месяц по среднему', format: 'text' },
]

/** Ключи tooltips из API (с дефисами, как в Django). */
export const OFFER_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  total: 'total',
  directions: 'directions',
  companies: 'companies',
  'avg-offer': 'avg-offer',
  'median-offer': 'median-offer',
  'max-offer': 'max-offer',
  'min-offer': 'min-offer',
  'popular-company': 'popular-company',
  'best-company': 'best-company',
  'best-month': 'best-month',
}
