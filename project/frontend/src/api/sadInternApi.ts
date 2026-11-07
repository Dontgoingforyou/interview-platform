import apiClient from './client'
import type {
  SadInternAnalytics,
  SadInternGroupedResponse,
  SadInternListItem,
  SadInternListFilters,
  SadInternOnProjectResponse,
  SadInternWritePayload,
} from '../types/sadIntern'
import {
  buildSadInternGroupedParams,
  buildSadInternOnProjectParams,
} from '../utils/sadIntern/sadInternListParams'

const BASE = '/api/sad-interns/'

export async function getSadInternAnalytics(): Promise<SadInternAnalytics> {
  const { data } = await apiClient.get<SadInternAnalytics>('/api/analytics/sad-intern/')
  return data
}

export async function getSadInternGrouped(
  filters: SadInternListFilters,
  directionsOffset: number,
  groupPages: Record<string, number>,
): Promise<SadInternGroupedResponse> {
  const params = buildSadInternGroupedParams(filters, directionsOffset, groupPages)
  const { data } = await apiClient.get<SadInternGroupedResponse>(`${BASE}grouped/`, { params })
  return data
}

export async function getSadInternOnProject(filters: SadInternListFilters): Promise<SadInternOnProjectResponse> {
  const params = buildSadInternOnProjectParams(filters)
  const { data } = await apiClient.get<SadInternOnProjectResponse>(`${BASE}on-project/`, { params })
  return data
}

export async function getSadIntern(id: number): Promise<SadInternListItem> {
  const { data } = await apiClient.get<SadInternListItem>(`${BASE}${id}/`)
  return data
}

export async function createSadIntern(payload: SadInternWritePayload): Promise<SadInternListItem> {
  const { data } = await apiClient.post<SadInternListItem>(BASE, payload)
  return data
}

export async function updateSadIntern(
  id: number,
  payload: Partial<SadInternWritePayload>,
): Promise<SadInternListItem> {
  const { data } = await apiClient.patch<SadInternListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteSadIntern(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function postSadInternImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>(`${BASE}import/`, body)
  return data
}
