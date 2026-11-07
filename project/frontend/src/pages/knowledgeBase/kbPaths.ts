/** Путь к просмотру статьи в SPA. */
export function kbArticlePath(sectionId: string, filename: string): string {
  return `/knowledge-base/${encodeURIComponent(sectionId)}/article/${encodeURIComponent(filename)}`
}

export function kbArticleNewPath(sectionId: string): string {
  return `/knowledge-base/${encodeURIComponent(sectionId)}/article/new`
}

export function kbArticleEditPath(sectionId: string, filename: string): string {
  return `/knowledge-base/${encodeURIComponent(sectionId)}/article/${encodeURIComponent(filename)}/edit`
}
