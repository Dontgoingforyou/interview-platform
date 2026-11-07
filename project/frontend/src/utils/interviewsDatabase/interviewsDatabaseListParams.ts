import { isInterviewsDatabaseTranscriptionFilterValue } from '../../constants/interviewsDatabaseTranscriptionFilter'
import type { InterviewsDatabaseListFilters } from '../../types/interview'
import type { OrderDir } from '../../types/common'

/** Плоские query-параметры для GET `/api/interviews-database/`. */
export function buildInterviewsDatabaseListParams(
  filters: InterviewsDatabaseListFilters,
): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.page != null) {
    params.page = filters.page
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.company != null) {
    params.company = filters.company
  }
  if (filters.direction_id != null) {
    params.direction_id = filters.direction_id
  }
  if (filters.interview_type) {
    params.interview_type = filters.interview_type
  }
  if (filters.transcription) {
    params.transcription = filters.transcription
  }
  if (filters.order_by) {
    params.order_by = filters.order_by
  }
  if (filters.order_dir) {
    params.order_dir = filters.order_dir
  }
  return params
}

/** Разбор URL страницы базы собеседований. */
export function parseInterviewsDatabaseListFromSearchParams(
  sp: URLSearchParams,
): InterviewsDatabaseListFilters {
  const page = Math.max(1, parseInt(sp.get('page') || '1', 10) || 1)
  const filters: InterviewsDatabaseListFilters = { page }
  const q = sp.get('q')
  if (q) {
    filters.q = q
  }
  const company = sp.get('company')
  if (company) {
    const n = parseInt(company, 10)
    if (!Number.isNaN(n)) {
      filters.company = n
    }
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
  const tr = sp.get('transcription')
  if (tr && isInterviewsDatabaseTranscriptionFilterValue(tr)) {
    filters.transcription = tr
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
