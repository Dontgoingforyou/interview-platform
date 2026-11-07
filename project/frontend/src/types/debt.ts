import type { OrderDir, Paginated } from './common'

/** Ответ GET `/api/analytics/debts/` */
export interface DebtAnalytics {
  total: number
  active: number
  closed: number
  'sum-total': number
  'sum-paid': number
  'sum-out': number
  'avg-out': number
  'avg-progress': number
  'top-out': number
  'top-out-person': string
  'no-payments': number
  tooltips: Record<string, string>
}

export type DebtRowHighlight = 'paid_fully' | 'not_paying' | 'default'

/** Элемент GET /api/debts/ */
export interface DebtListItem {
  id: number
  intern: number
  intern_name: string
  direction_id: number | null
  direction_name: string | null
  display_telegram: string
  display_email: string
  total_amount: string
  paid_amount: string
  balance: string
  payment_status: string
  act_date: string | null
  last_payment_month: number | null
  last_payment_year: number | null
  payments_four_months: Record<string, string>
  row_highlight: DebtRowHighlight
}

export type PaginatedDebts = Paginated<DebtListItem>

export interface DebtListFilters {
  page?: number
  page_size?: number
  q?: string
  direction?: number
  payment_status?: string
  intern_id?: number
  not_paid_filter?: string
  act_date_filter?: string
  act_date_from?: string
  act_date_to?: string
  order_by?: string
  order_dir?: OrderDir
}

export interface DebtListApiResponse extends PaginatedDebts {
  last_four_month_labels?: string[]
}

export interface PaymentHistoryItem {
  id: number
  month: number
  year: number
  amount: string
  created_at: string
}

/** GET /api/debts/:id/ */
export interface DebtDetail {
  id: number
  intern: number
  intern_name: string
  direction_id: number | null
  direction_name: string | null
  telegram_username: string | null
  email: string | null
  total_amount: string
  paid_amount: string
  balance: string
  payment_status: string
  act_date: string | null
  payment_history: PaymentHistoryItem[]
}

export interface DebtWritePayload {
  intern: number
  direction_id?: number | null
  telegram_username?: string | null
  email?: string | null
  total_amount?: string
  paid_amount?: string
  payment_status?: string
  act_date?: string | null
}

/** Элемент GET /api/debts/by-month/ */
export interface DebtByMonthRow {
  id: number
  intern_name: string
  direction_name: string | null
  total_amount: string
  paid_amount: string
  balance: string
  act_date: string | null
  payment_status: string
  payment_status_label: string
  total_period_amount: string
  period_amounts: Record<string, string>
  row_highlight: DebtRowHighlight
}

export interface DebtByMonthFilters {
  page?: number
  month_from?: number
  year_from?: number
  month_to?: number
  year_to?: number
  payment_status_filter?: string
}

export interface DebtByMonthApiResponse extends Paginated<DebtByMonthRow> {
  export_months: string[]
  selected_period: string
}
