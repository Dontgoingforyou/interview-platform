import { useEffect, useRef } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  deleteSadIntern,
  getSadInternAnalytics,
  getSadInternGrouped,
  getSadInternOnProject,
} from '../../api/sadInternApi'
import type { SadInternListFilters } from '../../types/sadIntern'
import type { AuthUser } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'
import { sadInternGroupedFilterKey } from '../../utils/sadIntern/sadInternListParams'
import { toast } from '../../utils/toast'

export function useSadInternListPage(filters: SadInternListFilters, user: AuthUser | null, groupPages: Record<string, number>) {
  const queryClient = useQueryClient()
  const isAdmin = isAdminUser(user)
  const filterKey = sadInternGroupedFilterKey(filters)

  const analyticsQuery = useQuery({
    queryKey: ['sad-intern', 'analytics'],
    queryFn: getSadInternAnalytics,
    staleTime: 60_000,
  })


  const groupedInfinite = useInfiniteQuery({
    queryKey: ['sad-intern', 'grouped', filterKey],
    queryFn: ({ pageParam }) => getSadInternGrouped(filters, pageParam as number, groupPages),
    initialPageParam: 0,
    getNextPageParam: (last) =>
      last.has_more_directions && last.next_directions_offset != null
        ? last.next_directions_offset
        : undefined,
    ...paginatedListQueryOptions,
  })

  // filterKey во ref, чтобы рефетч по страницам групп не зависел от смены фильтров
  const filterKeyRef = useRef(filterKey)
  const prevGroupPagesRef = useRef(groupPages)

  useEffect(() => {
    filterKeyRef.current = filterKey
  }, [filterKey])

  useEffect(() => {
    if (prevGroupPagesRef.current === groupPages) return
    prevGroupPagesRef.current = groupPages

    // Рефетч только если у запроса уже есть данные (не первый рендер)
    const hasData = queryClient.getQueryData(['sad-intern', 'grouped', filterKeyRef.current]) != null
    if (hasData) {
      void queryClient.refetchQueries({
        queryKey: ['sad-intern', 'grouped', filterKeyRef.current],
        type: 'active',
      })
    }
  }, [groupPages, queryClient])

  const mergedGroups = groupedInfinite.data?.pages.flatMap((p) => p.groups) ?? []

  const onProjectQuery = useQuery({
    queryKey: ['sad-intern', 'on-project', filterKey, filters.on_project_page],
    queryFn: () => getSadInternOnProject(filters),
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSadIntern,
    onSuccess: () => {
      toast.success('Запись удалена из списка ожидания')
      void queryClient.invalidateQueries({ queryKey: ['sad-intern'] })
    },
    onError: () => {
      toast.error('Не удалось удалить запись')
    },
  })

  return {
    analyticsQuery,
    groupedInfinite,
    mergedGroups,
    onProjectQuery,
    deleteMutation,
    isAdmin,
  }
}
