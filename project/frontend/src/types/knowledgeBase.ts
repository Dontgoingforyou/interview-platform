/** Раздел базы знаний (список). */
export interface KbSection {
  id: string
  title: string
  description: string
  icon: string
  order: number
  article_count: number
}

/** Элемент списка статей. */
export interface KbArticleListItem {
  filename: string
  title: string
  slug: string
}

/** Детали статьи с HTML с сервера (bleach). */
export interface KbArticleDetail {
  filename: string
  title: string
  markdown: string
  full_content: string
  html: string
  section_id: string
}

/** Результат полнотекстового поиска. */
export interface KbSearchHit {
  section_id: string
  section_title: string
  section_icon: string
  filename: string
  title: string
}

/** Ответ семантического поиска (vector_search). */
export interface SemanticSearchResultItem {
  entity_type: string
  entity_id: string | number
  text_content: string
  similarity_score: number
  metadata: Record<string, unknown>
}

export interface SemanticSearchResponse {
  query: string
  results: SemanticSearchResultItem[]
  total_found: number
  search_time_ms: number
}
