import type { InterviewListFilters } from '../../types/interview'
import type { OrderDir } from '../../types/common'

/**
 * Преобразует фильтры списка собеседований в плоский объект query-параметров для axios.
 * Имена query-параметров совпадают с GET `/api/interviews/`.
 */
export function buildInterviewListParams(
  filters: InterviewListFilters,
): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.date_from) {
    params.date_from = filters.date_from
  }
  if (filters.date_to) {
    params.date_to = filters.date_to
  }
  if (filters.date_filter) {
    params.date_filter = filters.date_filter
  }
  if (filters.interview_type) {
    params.interview_type = filters.interview_type
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.manager) {
    params.manager = filters.manager
  }
  if (filters.company != null) {
    params.company = filters.company
  }
  if (filters.interview_format) {
    params.interview_format = filters.interview_format
  }
  if (filters.has_video) {
    params.has_video = filters.has_video
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

/** Разбор query строки страницы списка собеседований в объект фильтров для API. */
export function parseInterviewListFromSearchParams(sp: URLSearchParams): InterviewListFilters {
  const page = Math.max(1, parseInt(sp.get('page') || '1', 10) || 1)
  const filters: InterviewListFilters = { page }
  const q = sp.get('q')
  if (q) {
    filters.q = q
  }
  const manager = sp.get('manager')
  if (manager) {
    filters.manager = manager
  }
  const company = sp.get('company')
  if (company) {
    const n = parseInt(company, 10)
    if (!Number.isNaN(n)) {
      filters.company = n
    }
  }
  const df = sp.get('date_from')
  const dt = sp.get('date_to')
  if (df) {
    filters.date_from = df
  }
  if (dt) {
    filters.date_to = dt
  }
  const dateFilter = sp.get('date_filter')
  if (dateFilter) {
    filters.date_filter = dateFilter
  }
  const directionRaw = sp.get('direction_id')
  if (directionRaw) {
    const n = parseInt(directionRaw, 10)
    if (!Number.isNaN(n)) {
      filters.direction_id = n
    }
  }
  const it = sp.get('interview_type')
  if (it) {
    filters.interview_type = it
  }
  const iff = sp.get('interview_format')
  if (iff) {
    filters.interview_format = iff
  }
  const hv = sp.get('has_video')
  if (hv === 'true' || hv === 'false') {
    filters.has_video = hv
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
