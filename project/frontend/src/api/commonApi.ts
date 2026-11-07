import apiClient from './client'

/** Опрос статуса асинхронной задачи импорта. URL общий для всех доменов. */
export async function getImportTaskStatus(taskId: string): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get(`/api/import/status/${taskId}/`)
  return data as Record<string, unknown>
}
