import { useQuery } from '@tanstack/react-query'

import {
  getDeveloperAnalytics,
  getDevelopersList,
  DEVELOPER_LIST_PAGE_SIZE,
} from '../../api/developersApi'
import type { DeveloperListFilters } from '../../types/developer'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

export function useDevelopersListPage(filters: DeveloperListFilters) {
  const analyticsQuery = useQuery({
    queryKey: ['developers', 'analytics'] as const,
    queryFn: getDeveloperAnalytics,
  })

  const listQuery = useQuery({
    queryKey: ['developers', 'list', filters] as const,
    queryFn: () => getDevelopersList(filters),
    ...paginatedListQueryOptions,
  })

  const paginated = listQuery.data
  const count = paginated?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / DEVELOPER_LIST_PAGE_SIZE))

  return {
    analyticsQuery,
    listQuery,
    count,
    totalPages,
    currentPage: filters.page,
    results: paginated?.results ?? [],
  }
}
