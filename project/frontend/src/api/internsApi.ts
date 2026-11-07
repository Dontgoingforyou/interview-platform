import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type {
  InternDetail,
  InternListFilters,
  InternListItem,
  InternWritePayload,
  PaginatedInterns,
} from '../types/intern'
import { buildInternListParams } from '../utils/interns/internListParams'

const BASE = '/api/interns/'

export const INTERN_LIST_PAGE_SIZE = 20

export async function getInterns(filters: InternListFilters): Promise<PaginatedInterns> {
  const params = buildInternListParams(filters)
  const { data } = await apiClient.get<PaginatedInterns | InternListItem[]>(BASE, { params })
  return normalizePaginatedResponse(data)
}

export async function getIntern(id: number): Promise<InternDetail> {
  const { data } = await apiClient.get<InternDetail>(`${BASE}${id}/`)
  return data
}

export async function createIntern(payload: InternWritePayload): Promise<InternListItem> {
  const { data } = await apiClient.post<InternListItem>(BASE, payload)
  return data
}

export async function updateIntern(
  id: number,
  payload: Partial<InternWritePayload>,
): Promise<InternListItem> {
  const { data } = await apiClient.patch<InternListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteIntern(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function patchInternManualStatus(
  id: number,
  manual_status: string,
): Promise<{ success: boolean; manual_status: string; status_display: string }> {
  const { data } = await apiClient.patch<{ success: boolean; manual_status: string; status_display: string }>(
    `${BASE}${id}/manual-status/`,
    { manual_status },
  )
  return data
}

export async function postInternImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>('/api/interns/import/', body)
  return data
}

export async function postInternImportDates(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>(
    '/api/interns/import-dates/',
    body,
  )
  return data
}

export async function postInternSyncImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>(
    '/api/interns/import-sync/',
    body,
  )
  return data
}
