import type { OrderDir, Paginated } from './common'

/** Ответ GET `/api/analytics/offers/` */
export interface OfferAnalytics {
  total: number
  directions: number
  companies: number
  'avg-offer': number
  'median-offer': number
  'max-offer': number
  'min-offer': number
  'popular-company': string
  'best-company': string
  'best-month': string
  tooltips: Record<string, string>
}

/** Элемент GET /api/offers/ */
export interface OfferListItem {
  id: number
  intern: number
  intern_name: string
  intern_telegram_username: string | null
  direction_id: number | null
  direction_name: string | null
  company: string | null
  amount: string | null
  month: number
  year: number
  created_at: string
}

export type PaginatedOffers = Paginated<OfferListItem>

/** Фильтры списка (URL + запросы к API). */
export interface OfferListFilters {
  page?: number
  page_size?: number
  q?: string
  direction_id?: number
  year?: number
  month?: number
  intern_id?: number
  order_by?: string
  order_dir?: OrderDir
}

export interface OfferMonthGroupRow {
  year: number
  month: number
  total_count: number
}

/** Ответ GET /api/offers/month-groups/ */
export interface OfferMonthGroupsResponse {
  groups: OfferMonthGroupRow[]
  offset: number
  limit: number
  has_more: boolean
  next_offset: number | null
}

/** GET /api/offers/:id/ */
export interface OfferDetail {
  id: number
  intern: number
  intern_name: string
  intern_telegram_username: string | null
  direction_id: number | null
  direction_name: string | null
  company: string | null
  amount: string | null
  month: number
  year: number
  created_at: string
  updated_at: string
}

export interface OfferWritePayload {
  intern: number
  direction_id: number
  company: string
  amount?: string | null
  month: number
  year: number
}
