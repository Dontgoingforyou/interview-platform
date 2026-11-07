import apiClient from './client'
import type {
  KbArticleDetail,
  KbArticleListItem,
  KbSearchHit,
  KbSection,
} from '../types/knowledgeBase'

const KB = '/api/knowledge-base'

export async function getKbSections(): Promise<KbSection[]> {
  const { data } = await apiClient.get<KbSection[]>(`${KB}/sections/`)
  return data
}

export async function getKbSection(sectionId: string): Promise<KbSection> {
  const { data } = await apiClient.get<KbSection>(`${KB}/sections/${encodeURIComponent(sectionId)}/`)
  return data
}

export async function createKbSection(payload: {
  section_id: string
  title: string
  description?: string
  icon?: string
}): Promise<{ section_id: string; title: string }> {
  const { data } = await apiClient.post(`${KB}/sections/`, payload)
  return data
}

export async function updateKbSection(
  sectionId: string,
  payload: { title?: string; description?: string; icon?: string },
): Promise<KbSection> {
  const { data } = await apiClient.patch(`${KB}/sections/${encodeURIComponent(sectionId)}/`, payload)
  return data
}

export async function deleteKbSection(sectionId: string): Promise<void> {
  await apiClient.delete(`${KB}/sections/${encodeURIComponent(sectionId)}/`)
}

export async function getKbArticles(sectionId: string): Promise<KbArticleListItem[]> {
  const { data } = await apiClient.get<KbArticleListItem[]>(
    `${KB}/sections/${encodeURIComponent(sectionId)}/articles/`,
  )
  return data
}

export async function getKbArticle(sectionId: string, filename: string): Promise<KbArticleDetail> {
  const { data } = await apiClient.get<KbArticleDetail>(
    `${KB}/sections/${encodeURIComponent(sectionId)}/articles/${encodeURIComponent(filename)}/`,
  )
  return data
}

export async function createKbArticle(
  sectionId: string,
  payload: { title: string; content?: string },
): Promise<{ filename: string; title: string }> {
  const { data } = await apiClient.post(
    `${KB}/sections/${encodeURIComponent(sectionId)}/articles/`,
    payload,
  )
  return data
}

export async function updateKbArticle(
  sectionId: string,
  filename: string,
  payload: { title?: string; content?: string },
): Promise<KbArticleDetail> {
  const { data } = await apiClient.patch(
    `${KB}/sections/${encodeURIComponent(sectionId)}/articles/${encodeURIComponent(filename)}/`,
    payload,
  )
  return data
}

export async function deleteKbArticle(sectionId: string, filename: string): Promise<void> {
  await apiClient.delete(
    `${KB}/sections/${encodeURIComponent(sectionId)}/articles/${encodeURIComponent(filename)}/`,
  )
}

export async function searchKbFullText(q: string): Promise<KbSearchHit[]> {
  const { data } = await apiClient.get<KbSearchHit[]>(`${KB}/search/`, { params: { q } })
  return data
}
