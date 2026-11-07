import apiClient from './client'
import type { DirectionMetricsResponse, DirectionObservationsResponse } from '../types/direction'

export async function getDirectionMetrics(
  params: Record<string, string | undefined>,
): Promise<DirectionMetricsResponse> {
  const { data } = await apiClient.get<DirectionMetricsResponse>('/api/analytics/directions/', {
    params,
  })
  return data
}

export async function getDirectionObservations(): Promise<DirectionObservationsResponse> {
  const { data } = await apiClient.get<DirectionObservationsResponse>('/api/observations/directions/')
  return data
}

export async function createDirection(payload: { name: string }): Promise<{ id: number; name: string }> {
  const { data } = await apiClient.post<{ id: number; name: string }>('/api/directions/', payload)
  return data
}
