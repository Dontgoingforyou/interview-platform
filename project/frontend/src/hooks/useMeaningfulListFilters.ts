import { useMemo } from 'react'

import { hasMeaningfulQueryFilters, LIST_PAGE_SORT_PAGINATION_KEYS } from '../utils/listPageSearchParams'

const DEFAULT_IGNORE = [...LIST_PAGE_SORT_PAGINATION_KEYS]

/**
 * Реактивный флаг: в query есть параметры кроме пагинации/сортировки (активные фильтры списка).
 * Передавайте стабильный литерал/константу модуля в `ignoreKeyList`, не `['page']` в JSX.
 */
export function useMeaningfulListFilters(
  searchParams: URLSearchParams,
  ignoreKeyList: readonly string[] = DEFAULT_IGNORE,
): boolean {
  const qs = searchParams.toString()
  const ignoreSerialized = JSON.stringify([...ignoreKeyList].sort())
  return useMemo(() => {
    const ignore = new Set(JSON.parse(ignoreSerialized) as string[])
    return hasMeaningfulQueryFilters(new URLSearchParams(qs), ignore)
  }, [qs, ignoreSerialized])
}
