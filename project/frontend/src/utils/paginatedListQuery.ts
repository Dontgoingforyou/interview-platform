import { keepPreviousData } from '@tanstack/react-query'

/**
 * Общие опции для пагинированных запросов: useQuery, useQueries, useInfiniteQuery.
 * При смене страницы, фильтров или ключа предыдущие данные остаются до ответа — без мигания UI.
 */
export const paginatedListQueryOptions = {
  placeholderData: keepPreviousData,
} as const
