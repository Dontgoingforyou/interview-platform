import { useQuery, type UseQueryOptions } from '@tanstack/react-query'

import { fetchInternPortalInterviews } from '../../api/internsPortalApi'
import type { InternPortalInterviewRow } from '../../types/internsPortal'
import type { Paginated } from '../../types/common'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

/** Список собеседований портала студента с пагинацией (page 1-based). */
export function useInternPortalList(
  page: number,
  options?: Omit<
    UseQueryOptions<Paginated<InternPortalInterviewRow>, Error, Paginated<InternPortalInterviewRow>>,
    'queryKey' | 'queryFn'
  >,
) {
  return useQuery({
    queryKey: ['interns-portal', 'interviews', page],
    queryFn: () => fetchInternPortalInterviews(page),
    ...paginatedListQueryOptions,
    ...options,
  })
}
