import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  deleteIntern,
  getInterns,
  INTERN_LIST_PAGE_SIZE,
  postInternImportDates,
  postInternSyncImport,
} from '../../api/internsApi'
import { getDirections, getManagersForFilters } from '../../api/referenceApi'
import type { InternListFilters } from '../../types/intern'
import { useAsyncFileImport } from '../useAsyncFileImport'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'
import { toast } from '../../utils/toast'

const INTERN_IMPORT_INVALIDATE: readonly (readonly unknown[])[] = [['interns']]

export function useInternsList(filters: InternListFilters) {
  const queryClient = useQueryClient()

  const syncImport = useAsyncFileImport(postInternSyncImport, INTERN_IMPORT_INVALIDATE)
  const datesImport = useAsyncFileImport(postInternImportDates, INTERN_IMPORT_INVALIDATE)

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const managersQuery = useQuery({
    queryKey: ['managers-for-filters'],
    queryFn: getManagersForFilters,
    staleTime: 300_000,
  })

  const listQuery = useQuery({
    queryKey: ['interns', 'list', filters],
    queryFn: () => getInterns(filters),
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteIntern(id),
    onSuccess: () => {
      toast.success('Студент удалён')
      void queryClient.invalidateQueries({ queryKey: ['interns'] })
    },
    onError: () => {
      toast.error('Не удалось удалить студента')
    },
  })

  const count = listQuery.data?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / INTERN_LIST_PAGE_SIZE))
  const currentPage = filters.page ?? 1
  const results = listQuery.data?.results ?? []

  return {
    directionsQuery,
    managersQuery,
    listQuery,
    deleteMutation,
    syncImport,
    datesImport,
    count,
    totalPages,
    currentPage,
    results,
  }
}
