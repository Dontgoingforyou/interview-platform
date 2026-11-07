import type { CompanyListFilters } from '../../types/company'

export const COMPANY_LIST_META_KEYS = new Set(['page', 'sort', 'q', 'bigtech'])

/** Ключи query, не участвующие в подсчёте «есть ли активные фильтры» на списке компаний. */
export const COMPANY_LIST_MEANINGFUL_FILTER_IGNORE = ['page', 'sort'] as const

/**
 * Парсинг query для страницы списка компаний.
 */
export function parseCompanyListFromSearchParams(searchParams: URLSearchParams): CompanyListFilters {
  const q = searchParams.get('q')?.trim() ?? ''
  const bigtechRaw = searchParams.get('bigtech') ?? ''
  const bigtech: '' | '0' | '1' =
    bigtechRaw === '1' || bigtechRaw === '0' ? (bigtechRaw as '0' | '1') : ''
  const sortRaw = searchParams.get('sort') ?? 'interviews'
  const sort: CompanyListFilters['sort'] =
    sortRaw === '-interviews' || sortRaw === 'name' || sortRaw === '-name' || sortRaw === 'interviews'
      ? sortRaw
      : 'interviews'
  const pageRaw = searchParams.get('page')
  const page = pageRaw ? Math.max(1, parseInt(pageRaw, 10) || 1) : 1
  return { q, bigtech, sort, page }
}
