import type { OrderDir } from '../../types/common'
import type { DebtListFilters } from '../../types/debt'

export const DEBT_LIST_DEFAULT_ORDER_BY = 'balance'
export const DEBT_LIST_DEFAULT_ORDER_DIR: OrderDir = 'desc'

export function buildDebtListParams(filters: DebtListFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.page_size != null) {
    params.page_size = filters.page_size
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.direction != null) {
    params.direction = filters.direction
  }
  if (filters.payment_status) {
    params.payment_status = filters.payment_status
  }
  if (filters.intern_id != null) {
    params.intern_id = filters.intern_id
  }
  if (filters.not_paid_filter) {
    params.not_paid_filter = filters.not_paid_filter
  }
  if (filters.act_date_filter) {
    params.act_date_filter = filters.act_date_filter
  }
  if (filters.act_date_from) {
    params.act_date_from = filters.act_date_from
  }
  if (filters.act_date_to) {
    params.act_date_to = filters.act_date_to
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

export function parseDebtListFromSearchParams(sp: URLSearchParams): DebtListFilters {
  const filters: DebtListFilters = {
    page: 1,
    order_by: DEBT_LIST_DEFAULT_ORDER_BY,
    order_dir: DEBT_LIST_DEFAULT_ORDER_DIR,
  }
  const pageRaw = sp.get('page')
  if (pageRaw) {
    const p = parseInt(pageRaw, 10)
    if (!Number.isNaN(p) && p >= 1) {
      filters.page = p
    }
  }
  const q = sp.get('q')
  if (q) {
    filters.q = q
  }
  const dir = sp.get('direction')
  if (dir) {
    const n = parseInt(dir, 10)
    if (!Number.isNaN(n)) {
      filters.direction = n
    }
  }
  const ps = sp.get('payment_status')
  if (ps) {
    filters.payment_status = ps
  }
  const np = sp.get('not_paid_filter')
  if (np) {
    filters.not_paid_filter = np
  }
  const adf = sp.get('act_date_filter')
  if (adf) {
    filters.act_date_filter = adf
  }
  const adFrom = sp.get('act_date_from')
  if (adFrom) {
    filters.act_date_from = adFrom
  }
  const adTo = sp.get('act_date_to')
  if (adTo) {
    filters.act_date_to = adTo
  }
  const ob = sp.get('order_by')
  if (ob) {
    filters.order_by = ob
  }
  const od = sp.get('order_dir')
  if (od === 'asc' || od === 'desc') {
    filters.order_dir = od as OrderDir
  }
  return filters
}
