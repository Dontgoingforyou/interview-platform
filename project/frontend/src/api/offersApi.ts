import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type {
  OfferAnalytics,
  OfferDetail,
  OfferListFilters,
  OfferListItem,
  OfferMonthGroupsResponse,
  OfferWritePayload,
  PaginatedOffers,
} from '../types/offer'
import {
  buildOfferListParams,
  buildOfferMonthGroupsBaseParams,
} from '../utils/offers/offerListParams'

const BASE = '/api/offers/'

export const OFFER_MONTH_PAGE_SIZE = 10
export const OFFER_MONTH_GROUPS_BATCH = 3

export async function getOfferAnalytics(): Promise<OfferAnalytics> {
  const { data } = await apiClient.get<OfferAnalytics>('/api/analytics/offers/')
  return data
}

export async function getOfferMonthGroups(
  filters: OfferListFilters,
  offset: number,
  limit: number,
): Promise<OfferMonthGroupsResponse> {
  const params: Record<string, string | number> = {
    ...buildOfferMonthGroupsBaseParams(filters),
    offset,
    limit,
  }
  const { data } = await apiClient.get<OfferMonthGroupsResponse>(`${BASE}month-groups/`, { params })
  return data
}

/**
 * Список офферов с пагинацией (для блока одного месяца — передавать year, month, page_size).
 */
export async function getOffers(filters: OfferListFilters): Promise<PaginatedOffers> {
  const params = buildOfferListParams(filters)
  const { data } = await apiClient.get<PaginatedOffers | OfferListItem[]>(BASE, { params })
  if (Array.isArray(data)) {
    return normalizePaginatedResponse(data)
  }
  return normalizePaginatedResponse(data)
}

export async function getOffer(id: number): Promise<OfferDetail> {
  const { data } = await apiClient.get<OfferDetail>(`${BASE}${id}/`)
  return data
}

export async function createOffer(payload: OfferWritePayload): Promise<OfferListItem> {
  const { data } = await apiClient.post<OfferListItem>(BASE, payload)
  return data
}

export async function updateOffer(
  id: number,
  payload: Partial<OfferWritePayload>,
): Promise<OfferListItem> {
  const { data } = await apiClient.patch<OfferListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteOffer(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function postOfferImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>(
    '/api/offers/import/',
    body,
  )
  return data
}
