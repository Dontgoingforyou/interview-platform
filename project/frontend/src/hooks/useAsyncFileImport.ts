import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'

import { getImportTaskStatus } from '../api/commonApi'
import { toast } from '../utils/toast'

type PostImportFn = (file: File) => Promise<{ status?: string; task_id?: string }>

/**
 * Общий поток: POST multipart → task_id → polling /api/import/status/ → invalidate + toast.
 */
export function useAsyncFileImport(
  postImport: PostImportFn,
  invalidateQueryKeyPrefixes: readonly (readonly unknown[])[],
) {
  const queryClient = useQueryClient()
  const invalidateRef = useRef(invalidateQueryKeyPrefixes)
  const [importTaskId, setImportTaskId] = useState<string | null>(null)

  useEffect(() => {
    invalidateRef.current = invalidateQueryKeyPrefixes
  }, [invalidateQueryKeyPrefixes])

  const importMutation = useMutation({
    mutationFn: postImport,
    onSuccess: (data) => {
      if (data.task_id) {
        setImportTaskId(data.task_id)
        toast.success('Импорт запущен')
      }
    },
    onError: () => {
      toast.error('Не удалось запустить импорт')
    },
  })

  const importStatusQuery = useQuery({
    queryKey: ['import-status', importTaskId],
    queryFn: () => getImportTaskStatus(importTaskId!),
    enabled: Boolean(importTaskId),
    refetchInterval: (q) => {
      const st = q.state.data?.state as string | undefined
      if (st === 'SUCCESS' || st === 'FAILURE') {
        return false
      }
      return 1500
    },
  })

  const importFinishHandledRef = useRef<string | null>(null)
  useEffect(() => {
    const tid = importTaskId
    const st = importStatusQuery.data?.state as string | undefined
    if (!tid || st !== 'SUCCESS') {
      return
    }
    const key = `${tid}:${st}`
    if (importFinishHandledRef.current === key) {
      return
    }
    importFinishHandledRef.current = key
    toast.success('Импорт завершён')
    for (const prefix of invalidateRef.current) {
      void queryClient.invalidateQueries({ queryKey: [...prefix] })
    }
  }, [importTaskId, importStatusQuery.data?.state, queryClient])

  return {
    importMutation,
    importStatusQuery,
    importTaskId,
    setImportTaskId,
  }
}
