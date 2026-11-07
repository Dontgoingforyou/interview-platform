import type { OrderDir } from '../../types/common'
import type { DeveloperListFilters } from '../../types/developer'

export const DEVELOPER_LIST_DEFAULT_ORDER_BY = 'full_name'
export const DEVELOPER_LIST_DEFAULT_ORDER_DIR: OrderDir = 'desc'

const VALID_ORDER_BY = new Set(['full_name', 'direction_name', 'last_activity', 'interview_count'])

export function buildDeveloperListParams(filters: DeveloperListFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {
    order_by: filters.order_by,
    order_dir: filters.order_dir,
  }
  if (filters.page != null && filters.page > 1) {
    params.page = filters.page
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  return params
}

/** Параметры для экспорта таблицы (без page). */
export function buildDeveloperTableExportParams(
  filters: DeveloperListFilters,
): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

export function parseDeveloperListFromSearchParams(sp: URLSearchParams): DeveloperListFilters {
  const filters: DeveloperListFilters = {
    page: 1,
    order_by: DEVELOPER_LIST_DEFAULT_ORDER_BY,
    order_dir: DEVELOPER_LIST_DEFAULT_ORDER_DIR,
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
  const dirRaw = sp.get('direction_id') ?? sp.get('direction')
  if (dirRaw) {
    const d = parseInt(dirRaw, 10)
    if (!Number.isNaN(d)) {
      filters.direction_id = d
    }
  }
  const ob = sp.get('order_by')
  if (ob && VALID_ORDER_BY.has(ob)) {
    filters.order_by = ob
  }
  const od = sp.get('order_dir')
  if (od === 'asc' || od === 'desc') {
    filters.order_dir = od
  }
  return filters
}
