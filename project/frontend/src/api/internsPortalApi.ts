import { INTERN_PORTAL_UPLOAD_TIMEOUT_MS } from '../constants/internsPortal'
import type { InternPortalInterviewRow, InternPortalUploadTaskStatus } from '../types/internsPortal'
import type { Paginated } from '../types/common'
import apiClient from './client'

/** Пагинированный список собеседований студента. */
export async function fetchInternPortalInterviews(page: number): Promise<Paginated<InternPortalInterviewRow>> {
  const { data } = await apiClient.get<Paginated<InternPortalInterviewRow>>('/api/interns-portal/interviews/', {
    params: { page },
  })
  return data
}

/** POST multipart: старт загрузки видео в S3. */
export async function uploadInternPortalVideo(
  interviewId: number,
  file: File,
  onUploadProgress?: (pct: number) => void,
): Promise<{ task_id: string }> {
  const form = new FormData()
  form.append('video', file)
  const { data } = await apiClient.post<{ task_id: string }>(
    `/api/interns-portal/interviews/${interviewId}/upload/`,
    form,
    {
      timeout: INTERN_PORTAL_UPLOAD_TIMEOUT_MS,
      // null удаляет дефолтный Content-Type: application/json из apiClient,
      // чтобы браузер сам выставил multipart/form-data с корректным boundary
      headers: { 'Content-Type': null },
      onUploadProgress: onUploadProgress
        ? (evt) => {
            if (evt.total) {
              onUploadProgress(Math.round((evt.loaded / evt.total) * 100))
            }
          }
        : undefined,
    },
  )
  return data
}

/** Прогресс Celery только для своей задачи загрузки. */
export async function fetchInternPortalUploadTaskStatus(taskId: string): Promise<InternPortalUploadTaskStatus> {
  const { data } = await apiClient.get<InternPortalUploadTaskStatus>(
    `/api/interns-portal/upload-tasks/${taskId}/`,
  )
  return data
}
