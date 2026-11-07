import apiClient from './client'
import type { SemanticSearchResponse } from '../types/knowledgeBase'

export async function postSemanticSearch(payload: {
  query: string
  entity_type?: string
  top_k?: number
}): Promise<SemanticSearchResponse> {
  const { data } = await apiClient.post<SemanticSearchResponse>('/api/vector/search/', payload)
  return data
}
