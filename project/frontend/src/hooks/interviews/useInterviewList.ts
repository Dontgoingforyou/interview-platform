import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  deleteInterview,
  getDeepgramBalance,
  getInterviewAnalytics,
  getInterviewTypeBreakdown,
  getInterviews,
  INTERVIEW_LIST_PAGE_SIZE,
  postInterviewImport,
} from '../../api/interviewsApi'
import { getDirections, getManagersForFilters } from '../../api/referenceApi'
import type { InterviewListFilters } from '../../types/interview'
import { useAsyncFileImport } from '../useAsyncFileImport'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'
import { toast } from '../../utils/toast'

const INTERVIEW_IMPORT_INVALIDATE: readonly (readonly unknown[])[] = [
  ['interviews'],
  ['interview-analytics'],
  ['interview-type-breakdown'],
]

export function useInterviewList(filters: InterviewListFilters, isAdmin: boolean) {
  const queryClient = useQueryClient()
  const {
    importMutation,
    importStatusQuery,
    importTaskId,
    setImportTaskId,
  } = useAsyncFileImport(postInterviewImport, INTERVIEW_IMPORT_INVALIDATE)

  const analyticsQuery = useQuery({
    queryKey: ['interview-analytics'],
    queryFn: getInterviewAnalytics,
    staleTime: 60_000,
  })

  const typeBreakdownQuery = useQuery({
    queryKey: ['interview-type-breakdown', filters],
    queryFn: () => getInterviewTypeBreakdown(filters),
    staleTime: 30_000,
  })

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

  const deepgramQuery = useQuery({
    queryKey: ['deepgram-balance'],
    queryFn: getDeepgramBalance,
    enabled: isAdmin,
    staleTime: 120_000,
  })

  const listQuery = useQuery({
    queryKey: ['interviews', filters],
    queryFn: () => getInterviews(filters),
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteInterview(id),
    onSuccess: () => {
      toast.success('Запись удалена')
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
      void queryClient.invalidateQueries({ queryKey: ['interview-analytics'] })
      void queryClient.invalidateQueries({ queryKey: ['interview-type-breakdown'] })
    },
    onError: () => {
      toast.error('Не удалось удалить')
    },
  })

  const count = listQuery.data?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / INTERVIEW_LIST_PAGE_SIZE))
  const currentPage = filters.page ?? 1
  const results = listQuery.data?.results ?? []

  return {
    analyticsQuery,
    typeBreakdownQuery,
    directionsQuery,
    managersQuery,
    deepgramQuery,
    listQuery,
    deleteMutation,
    importMutation,
    importStatusQuery,
    importTaskId,
    setImportTaskId,
    count,
    totalPages,
    currentPage,
    results,
  }
}
