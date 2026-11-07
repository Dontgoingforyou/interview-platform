import { Link, useParams } from 'react-router-dom'

import KbArticleHtml from '../../components/knowledgeBase/KbArticleHtml'
import KnowledgeBaseBreadcrumbs from '../../components/knowledgeBase/KnowledgeBaseBreadcrumbs'
import { InlineError, LoadingLine, PageTitle } from '../../components/ui'
import { useKbArticleQuery, useKbSectionQuery } from '../../hooks/knowledgeBase/useKnowledgeBaseQueries'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { kbArticleEditPath } from './kbPaths'

/**
 * Просмотр статьи (HTML с сервера после bleach).
 */
function KnowledgeBaseArticlePage() {
  const { sectionId: sectionIdParam, filename: filenameParam } = useParams<{
    sectionId: string
    filename: string
  }>()
  const sectionId = sectionIdParam ? decodeURIComponent(sectionIdParam) : ''
  const filename = filenameParam ? decodeURIComponent(filenameParam) : ''
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const articleQuery = useKbArticleQuery(sectionId || undefined, filename || undefined)
  const sectionQuery = useKbSectionQuery(sectionId || undefined)

  if (!sectionId || !filename) {
    return <InlineError message="Некорректный адрес статьи" />
  }

  if (articleQuery.isLoading || sectionQuery.isLoading) {
    return <LoadingLine message="Загрузка статьи…" />
  }

  if (articleQuery.isError || !articleQuery.data) {
    return <InlineError message="Статья не найдена" />
  }

  const article = articleQuery.data
  const sectionTitle = sectionQuery.data?.title ?? sectionId

  return (
    <div className="kb-page kb-article-view">
      <KnowledgeBaseBreadcrumbs
        items={[
          { label: 'База знаний', to: '/knowledge-base' },
          { label: sectionTitle, to: `/knowledge-base?section=${encodeURIComponent(sectionId)}` },
          { label: article.title },
        ]}
      />
      <div className="kb-article-view-head">
        <PageTitle>{article.title}</PageTitle>
        {isAdmin && (
          <Link className="btn btn-secondary btn-small" to={kbArticleEditPath(sectionId, filename)}>
            Редактировать
          </Link>
        )}
      </div>
      <div className="kb-article-body">
        <KbArticleHtml html={article.html} />
      </div>
    </div>
  )
}

export default KnowledgeBaseArticlePage
