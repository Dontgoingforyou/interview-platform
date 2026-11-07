import { useQuery } from '@tanstack/react-query'

import {
  getKbArticle,
  getKbArticles,
  getKbSection,
  getKbSections,
  searchKbFullText,
} from '../../api/knowledgeBaseApi'

export const kbQueryKeys = {
  sections: ['knowledgeBase', 'sections'] as const,
  section: (id: string) => ['knowledgeBase', 'section', id] as const,
  articles: (sectionId: string) => ['knowledgeBase', 'articles', sectionId] as const,
  article: (sectionId: string, filename: string) =>
    ['knowledgeBase', 'article', sectionId, filename] as const,
  search: (q: string) => ['knowledgeBase', 'search', q] as const,
}

export function useKbSectionsQuery() {
  return useQuery({
    queryKey: kbQueryKeys.sections,
    queryFn: () => getKbSections(),
  })
}

export function useKbSectionQuery(sectionId: string | undefined) {
  return useQuery({
    queryKey: kbQueryKeys.section(sectionId ?? ''),
    queryFn: () => getKbSection(sectionId!),
    enabled: Boolean(sectionId),
  })
}

export function useKbArticlesQuery(sectionId: string | undefined) {
  return useQuery({
    queryKey: kbQueryKeys.articles(sectionId ?? ''),
    queryFn: () => getKbArticles(sectionId!),
    enabled: Boolean(sectionId),
  })
}

export function useKbArticleQuery(sectionId: string | undefined, filename: string | undefined) {
  return useQuery({
    queryKey: kbQueryKeys.article(sectionId ?? '', filename ?? ''),
    queryFn: () => getKbArticle(sectionId!, filename!),
    enabled: Boolean(sectionId && filename),
  })
}

export function useKbFullTextSearchQuery(debouncedQ: string) {
  const q = debouncedQ.trim()
  return useQuery({
    queryKey: kbQueryKeys.search(q),
    queryFn: () => searchKbFullText(q),
    enabled: q.length > 0,
  })
}
