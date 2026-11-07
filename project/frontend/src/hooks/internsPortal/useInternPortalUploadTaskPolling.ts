import { useEffect, useState } from 'react'
import type { QueryClient } from '@tanstack/react-query'

import { fetchInternPortalUploadTaskStatus } from '../../api/internsPortalApi'
import type { InternPortalInterviewRow } from '../../types/internsPortal'
import { internPortalCeleryFailureMessage } from '../../utils/internsPortal/uploadErrors'

/** Как в legacy `interns-portal.js` (POLL_INTERVAL_MS). */
const POLL_INTERVAL_MS = 3000

export type InternPortalUploadProgressEntry = {
  percent: number
  statusText: string
  error?: string
}

/**
 * Опрос Celery по `upload_task_id` для строк в состоянии «uploading» —
 * обновляет процент и текст.
 */
export function useInternPortalUploadTaskPolling(
  rows: InternPortalInterviewRow[],
  queryClient: QueryClient,
): Record<number, InternPortalUploadProgressEntry> {
  const [progressByInterviewId, setProgressByInterviewId] = useState<
    Record<number, InternPortalUploadProgressEntry>
  >({})

  useEffect(() => {
    const active = rows
      .filter((r) => r.upload_task_id && r.upload_action_state === 'uploading')
      .map((r) => ({ interviewId: r.id, taskId: r.upload_task_id as string }))

    if (active.length === 0) {
      const clearId = window.setTimeout(() => {
        setProgressByInterviewId((prev) => (Object.keys(prev).length === 0 ? prev : {}))
      }, 0)
      return () => window.clearTimeout(clearId)
    }

    let cancelled = false

    const pollOnce = async () => {
      await Promise.all(
        active.map(async ({ interviewId, taskId }) => {
          try {
            const data = await fetchInternPortalUploadTaskStatus(taskId)
            if (cancelled) {
              return
            }
            if (data.state === 'SUCCESS') {
              setProgressByInterviewId((prev) => {
                const next = { ...prev }
                delete next[interviewId]
                return next
              })
              void queryClient.invalidateQueries({ queryKey: ['interns-portal', 'interviews'] })
              return
            }
            if (data.state === 'FAILURE') {
              const msg = internPortalCeleryFailureMessage(data.status)
              setProgressByInterviewId((prev) => ({
                ...prev,
                [interviewId]: { percent: 0, statusText: msg, error: msg },
              }))
              void queryClient.invalidateQueries({ queryKey: ['interns-portal', 'interviews'] })
              return
            }
            const percent = Math.min(100, Math.max(0, data.current ?? 0))
            const statusText =
              data.state === 'PENDING'
                ? 'Ожидание начала загрузки...'
                : (data.status?.trim() || 'Загрузка в облако…')
            setProgressByInterviewId((prev) => ({
              ...prev,
              [interviewId]: { percent, statusText },
            }))
          } catch {
            /* сеть — повторим по интервалу */
          }
        }),
      )
    }

    void pollOnce()
    const timer = window.setInterval(() => {
      void pollOnce()
    }, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [rows, queryClient])

  return progressByInterviewId
}
