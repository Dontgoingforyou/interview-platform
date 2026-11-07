import type { OrderDir } from './common'

/** Параметры списка «грустят» (URL + запросы к API). */
export interface SadInternListFilters {
  q?: string
  status?: string
  direction?: number | null
  order_by: string
  order_dir: OrderDir
  on_project_page: number
}

export interface SadInternAnalytics {
  total: number
  with_contact: number
  avg_wait: number
  longest_wait_days: number
  longest_wait_name: string
  tooltips: Record<string, string>
}

export interface SadInternListItem {
  id: number
  intern: number
  intern_name: string
  real_interview_date: string | null
  direction_id: number | null
  direction_name: string | null
  date_added: string
  waiting_since: string
  days_waiting: number
  telegram_username: string | null
  manager_email: string | null
  intern_manager_name: string | null
  status: string | null
  status_display: string | null
  note: string | null
}

export interface SadInternGroupedGroup {
  direction_id: number | null
  direction_name: string
  page: number
  total_pages: number
  total_count: number
  per_page: number
  pagination_key: string
  results: SadInternListItem[]
}

export interface SadInternGroupedResponse {
  groups: SadInternGroupedGroup[]
  has_more_directions: boolean
  next_directions_offset: number | null
  total_directions: number
  directions_offset: number
}

export interface SadInternOnProjectResponse {
  count: number
  page: number
  total_pages: number
  results: SadInternListItem[]
}

export interface SadInternWritePayload {
  intern: number
  waiting_since?: string
  telegram_username?: string | null
  manager_email?: string | null
  status?: string | null
  note?: string | null
}
