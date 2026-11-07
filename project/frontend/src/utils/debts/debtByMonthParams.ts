import type { DebtByMonthFilters } from '../../types/debt'

export function buildDebtByMonthParams(filters: DebtByMonthFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.month_from != null) {
    params.month_from = filters.month_from
  }
  if (filters.year_from != null) {
    params.year_from = filters.year_from
  }
  if (filters.month_to != null) {
    params.month_to = filters.month_to
  }
  if (filters.year_to != null) {
    params.year_to = filters.year_to
  }
  if (filters.payment_status_filter) {
    params.payment_status_filter = filters.payment_status_filter
  }
  return params
}

export function parseDebtByMonthFromSearchParams(sp: URLSearchParams): DebtByMonthFilters {
  const filters: DebtByMonthFilters = { page: 1 }
  const pageRaw = sp.get('page')
  if (pageRaw) {
    const p = parseInt(pageRaw, 10)
    if (!Number.isNaN(p) && p >= 1) {
      filters.page = p
    }
  }
  const mf = sp.get('month_from')
  const yf = sp.get('year_from')
  const mt = sp.get('month_to')
  const yt = sp.get('year_to')
  if (mf) {
    const n = parseInt(mf, 10)
    if (!Number.isNaN(n)) {
      filters.month_from = n
    }
  }
  if (yf) {
    const n = parseInt(yf, 10)
    if (!Number.isNaN(n)) {
      filters.year_from = n
    }
  }
  if (mt) {
    const n = parseInt(mt, 10)
    if (!Number.isNaN(n)) {
      filters.month_to = n
    }
  }
  if (yt) {
    const n = parseInt(yt, 10)
    if (!Number.isNaN(n)) {
      filters.year_to = n
    }
  }
  const psf = sp.get('payment_status_filter')
  if (psf) {
    filters.payment_status_filter = psf
  }
  return filters
}
