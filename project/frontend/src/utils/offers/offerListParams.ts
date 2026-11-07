import type { OrderDir } from '../../types/common'
import type { OfferListFilters } from '../../types/offer'

export const OFFER_LIST_DEFAULT_ORDER_BY = 'year'
export const OFFER_LIST_DEFAULT_ORDER_DIR: OrderDir = 'desc'

/** Параметры для GET /api/offers/month-groups/ (без offset/limit — задаются отдельно). */
export function buildOfferMonthGroupsBaseParams(
  filters: OfferListFilters,
): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.q) {
    params.search = filters.q
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  if (filters.year != null) {
    params.year = filters.year
  }
  if (filters.month != null) {
    params.month = filters.month
  }
  if (filters.intern_id != null) {
    params.intern_id = filters.intern_id
  }
  return params
}

export function buildOfferListParams(filters: OfferListFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {
    ...buildOfferMonthGroupsBaseParams(filters),
  }
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.page_size != null) {
    params.page_size = filters.page_size
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

export function parseOfferListFromSearchParams(sp: URLSearchParams): OfferListFilters {
  const filters: OfferListFilters = {
    order_by: OFFER_LIST_DEFAULT_ORDER_BY,
    order_dir: OFFER_LIST_DEFAULT_ORDER_DIR,
  }
  const q = sp.get('q')
  if (q) {
    filters.q = q
  }
  const dir = sp.get('direction_id')
  if (dir) {
    const n = parseInt(dir, 10)
    if (!Number.isNaN(n)) {
      filters.direction_id = n
    }
  }
  const y = sp.get('year')
  if (y) {
    const n = parseInt(y, 10)
    if (!Number.isNaN(n)) {
      filters.year = n
    }
  }
  const m = sp.get('month')
  if (m) {
    const n = parseInt(m, 10)
    if (!Number.isNaN(n)) {
      filters.month = n
    }
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
