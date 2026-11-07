import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { createKbArticle, updateKbArticle } from '../../api/knowledgeBaseApi'
import KnowledgeBaseBreadcrumbs from '../../components/knowledgeBase/KnowledgeBaseBreadcrumbs'
import { InlineError, LoadingLine, PageTitle } from '../../components/ui'
import { kbQueryKeys, useKbArticleQuery, useKbSectionQuery } from '../../hooks/knowledgeBase/useKnowledgeBaseQueries'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'
import KnowledgeBaseArticleFormFields from './KnowledgeBaseArticleFormFields'
import { kbArticlePath } from './kbPaths'

/**
 * Создание или редактирование статьи (Markdown + живое превью).
 */
function KnowledgeBaseArticleFormPage({ mode }: { mode: 'create' | 'edit' }) {
  const { sectionId: sectionIdParam, filename: filenameParam } = useParams<{
    sectionId: string
    filename: string
  }>()
  const sectionId = sectionIdParam ? decodeURIComponent(sectionIdParam) : ''
  const filename = filenameParam ? decodeURIComponent(filenameParam) : ''
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const articleQuery = useKbArticleQuery(
    mode === 'edit' ? sectionId : undefined,
    mode === 'edit' ? filename : undefined,
  )
  const sectionQuery = useKbSectionQuery(sectionId || undefined)

  const createMutation = useMutation({
    mutationFn: (payload: { title: string; content: string }) =>
      createKbArticle(sectionId, { title: payload.title, content: payload.content }),
    onSuccess: (data) => {
      toast.success('Статья создана')
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.sections })
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.articles(sectionId) })
      navigate(kbArticlePath(sectionId, data.filename))
    },
    onError: () => toast.error('Не удалось создать статью'),
  })

  const updateMutation = useMutation({
    mutationFn: (payload: { title: string; content: string }) =>
      updateKbArticle(sectionId, filename, { title: payload.title, content: payload.content }),
    onSuccess: () => {
      toast.success('Статья сохранена')
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.article(sectionId, filename) })
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.articles(sectionId) })
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.sections })
      navigate(kbArticlePath(sectionId, filename))
    },
    onError: () => toast.error('Не удалось сохранить статью'),
  })

  if (!isAdmin) {
    return <Navigate to="/knowledge-base" replace />
  }

  if (!sectionId) {
    return <InlineError message="Не указан раздел" />
  }

  if (mode === 'edit' && (!filename || articleQuery.isError)) {
    return <InlineError message="Статья не найдена" />
  }

  if (mode === 'edit' && articleQuery.isLoading) {
    return <LoadingLine message="Загрузка…" />
  }

  const sectionTitle = sectionQuery.data?.title ?? sectionId
  const pending = createMutation.isPending || updateMutation.isPending

  const formKey =
    mode === 'create' ? `create-${sectionId}` : `edit-${sectionId}-${filename}`

  return (
    <div className="kb-page">
      <KnowledgeBaseBreadcrumbs
        items={[
          { label: 'База знаний', to: '/knowledge-base' },
          { label: sectionTitle, to: `/knowledge-base?section=${encodeURIComponent(sectionId)}` },
          { label: mode === 'create' ? 'Новая статья' : 'Редактирование' },
        ]}
      />
      <PageTitle>{mode === 'create' ? 'Создание статьи' : 'Редактирование статьи'}</PageTitle>

      {mode === 'create' && (
        <KnowledgeBaseArticleFormFields
          key={formKey}
          mode="create"
          sectionId={sectionId}
          filename=""
          initialTitle=""
          initialContent=""
          pending={pending}
          onSubmit={(payload) => createMutation.mutate(payload)}
        />
      )}

      {mode === 'edit' && articleQuery.data && (
        <KnowledgeBaseArticleFormFields
          key={formKey}
          mode="edit"
          sectionId={sectionId}
          filename={filename}
          initialTitle={articleQuery.data.title}
          initialContent={articleQuery.data.markdown}
          pending={pending}
          onSubmit={(payload) => updateMutation.mutate(payload)}
        />
      )}
    </div>
  )
}

export default KnowledgeBaseArticleFormPage
