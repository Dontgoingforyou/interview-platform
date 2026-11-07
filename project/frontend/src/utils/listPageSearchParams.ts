/** Ключи query, не считающиеся «фильтрами» для сводки «активные фильтры». */
export const LIST_PAGE_SORT_PAGINATION_KEYS = new Set(['page', 'order_by', 'order_dir'])

/**
 * Есть ли в URL параметры кроме пагинации и сортировки.
 */
export function hasMeaningfulQueryFilters(
  searchParams: URLSearchParams,
  ignoreKeys: Set<string> = LIST_PAGE_SORT_PAGINATION_KEYS,
): boolean {
  for (const key of searchParams.keys()) {
    if (ignoreKeys.has(key)) {
      continue
    }
    const v = searchParams.get(key)
    if (v != null && v !== '') {
      return true
    }
  }
  return false
}

/**
 * Клонирует query, применяет мутацию и возвращает новый объект (для setSearchParams).
 */
export function withClonedSearchParams(
  current: URLSearchParams,
  mut: (next: URLSearchParams) => void,
): URLSearchParams {
  const next = new URLSearchParams(current)
  mut(next)
  return next
}

/**
 * Переключение сортировки таблицы в query (сброс page на 1).
 * @param newColumnDirection — `order_dir` при переходе на другую колонку (`asc` — студенты, `desc` — собеседования).
 */
export function applyTableSortToSearchParams(
  p: URLSearchParams,
  field: string,
  newColumnDirection: 'asc' | 'desc',
): void {
  const cur = p.get('order_by')
  const normalized = p.get('order_dir') === 'asc' ? 'asc' : 'desc'
  if (cur === field) {
    p.set('order_dir', normalized === 'asc' ? 'desc' : 'asc')
  } else {
    p.set('order_by', field)
    p.set('order_dir', newColumnDirection)
  }
  p.set('page', '1')
}
