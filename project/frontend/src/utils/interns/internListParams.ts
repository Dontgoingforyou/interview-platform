import type { OrderDir } from '../../types/common'
import type { InternListFilters } from '../../types/intern'

export function buildInternListParams(filters: InternListFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.status) {
    params.status = filters.status
  }
  if (filters.manager) {
    params.manager = filters.manager
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  if (filters.group) {
    params.group = filters.group
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

/** Разбор query страницы списка студентов. */
export function parseInternListFromSearchParams(sp: URLSearchParams): InternListFilters {
  const filters: InternListFilters = { page: 1, order_by: 'id', order_dir: 'desc' }
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
  const st = sp.get('status')
  if (st) {
    filters.status = st
  }
  const manager = sp.get('manager')
  if (manager) {
    filters.manager = manager
  }
  const dir = sp.get('direction_id')
  if (dir) {
    const n = parseInt(dir, 10)
    if (!Number.isNaN(n)) {
      filters.direction_id = n
    }
  }
  const group = sp.get('group')
  if (group) {
    filters.group = group
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
