/**
 * Единое оформление фонового обновления таблиц/списков (без мигания данных в React Query).
 * Стили класса — в `styles/list-pages.css` (подключается через `index.css`).
 */
export const LIST_DATA_REFRESHING_CLASS = 'list-data-refreshing'

/** Добавляет класс приглушения, если идёт refetch при уже загруженных данных. */
export function withListDataRefreshingClass(baseClassName: string, isRefreshing: boolean): string {
  const base = baseClassName.trim()
  if (!isRefreshing) {
    return base
  }
  return base ? `${base} ${LIST_DATA_REFRESHING_CLASS}` : LIST_DATA_REFRESHING_CLASS
}

/** Удобная проверка для useQuery: фоновое обновление, не первый запрос. */
export function isListBackgroundRefetch(isFetching: boolean, hasData: boolean): boolean {
  return Boolean(isFetching && hasData)
}
