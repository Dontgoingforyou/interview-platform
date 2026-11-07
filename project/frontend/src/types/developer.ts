import type { OrderDir, Paginated } from './common'

/** Строка списка разработчиков (GET /api/developers/). */
export interface DeveloperStatRow {
  intern_id: number
  intern_name: string
  direction_id: number | null
  direction_name: string | null
  interview_count: number
  first_interview_date: string | null
  last_interview_date: string | null
  id: number
  full_name: string
  email: string | null
}

export type PaginatedDevelopers = Paginated<DeveloperStatRow>

/** Аналитика разработчиков (GET /api/analytics/developers/). */
export interface DeveloperAnalytics {
  'active-specialists': number
  'offers-this-year': number
  'avg-offer-last-month': number
  'fastest-direction': string
  'fastest-direction-days': number | null
  'top-direction-offers': string
  chart_months: {
    labels: string[]
    data: number[]
  }
  tooltips: Record<string, string>
}

export interface DeveloperListFilters {
  page: number
  q?: string
  direction_id?: number | null
  order_by: string
  order_dir: OrderDir
}
