import { useQuery } from '@tanstack/react-query'

import {
  getInterviewsDatabaseList,
  INTERVIEWS_DATABASE_PAGE_SIZE,
} from '../../api/interviewsDatabaseApi'
import type { InterviewsDatabaseListFilters } from '../../types/interview'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

export function useInterviewsDatabaseList(filters: InterviewsDatabaseListFilters) {
  const listQuery = useQuery({
    queryKey: ['interviews-database', 'list', filters],
    queryFn: () => getInterviewsDatabaseList(filters),
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const count = listQuery.data?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / INTERVIEWS_DATABASE_PAGE_SIZE))
  const currentPage = filters.page ?? 1
  const results = listQuery.data?.results ?? []

  return {
    listQuery,
    totalPages,
    currentPage,
    results,
  }
}
