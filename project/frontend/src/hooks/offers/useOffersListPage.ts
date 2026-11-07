import { useInfiniteQuery, useQueries, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import {
  getOfferAnalytics,
  getOfferMonthGroups,
  getOffers,
  OFFER_MONTH_GROUPS_BATCH,
  OFFER_MONTH_PAGE_SIZE,
} from '../../api/offersApi'
import type { OfferListFilters, OfferMonthGroupRow } from '../../types/offer'
import type { AuthUser } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

function monthKey(g: OfferMonthGroupRow): string {
  return `${g.year}-${g.month}`
}

/**
 * Аналитика + бесконечная подгрузка групп месяцев + постраничные списки по каждому месяцу.
 */
export function useOffersListPage(
  filters: OfferListFilters,
  pageByMonth: Record<string, number>,
  user: AuthUser | null,
) {
  const isAdmin = isAdminUser(user)

  const analyticsQuery = useQuery({
    queryKey: ['offers', 'analytics'],
    queryFn: getOfferAnalytics,
    staleTime: 60_000,
  })

  const monthGroupsInfinite = useInfiniteQuery({
    queryKey: ['offers', 'month-groups', filters],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      getOfferMonthGroups(filters, pageParam as number, OFFER_MONTH_GROUPS_BATCH),
    getNextPageParam: (last) =>
      last.has_more && last.next_offset != null ? last.next_offset : undefined,
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const groups: OfferMonthGroupRow[] = useMemo(
    () => monthGroupsInfinite.data?.pages.flatMap((p) => p.groups) ?? [],
    [monthGroupsInfinite.data?.pages],
  )

  const listQueries = useQueries({
    queries: groups.map((g) => {
      const key = monthKey(g)
      const page = pageByMonth[key] ?? 1
      return {
        queryKey: ['offers', 'list', g.year, g.month, page, filters],
        queryFn: () =>
          getOffers({
            ...filters,
            year: g.year,
            month: g.month,
            page,
            page_size: OFFER_MONTH_PAGE_SIZE,
          }),
        staleTime: 30_000,
        ...paginatedListQueryOptions,
      }
    }),
  })

  return {
    isAdmin,
    analyticsQuery,
    monthGroupsInfinite,
    groups,
    listQueries,
  }
}
