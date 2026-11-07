import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import MarkdownGuideSidebar from '../../components/knowledgeBase/MarkdownGuideSidebar'
import MarkdownLivePreview from '../../components/knowledgeBase/MarkdownLivePreview'
import { toast } from '../../utils/toast'
import { kbArticlePath } from './kbPaths'

interface KnowledgeBaseArticleFormFieldsProps {
  mode: 'create' | 'edit'
  sectionId: string
  filename: string
  initialTitle: string
  initialContent: string
  onSubmit: (payload: { title: string; content: string }) => void
  pending: boolean
}

/**
 * Поля формы статьи: key на родителе сбрасывает state при смене статьи/режима.
 */
function KnowledgeBaseArticleFormFields({
  mode,
  sectionId,
  filename,
  initialTitle,
  initialContent,
  onSubmit,
  pending,
}: KnowledgeBaseArticleFormFieldsProps) {
  const navigate = useNavigate()
  const [title, setTitle] = useState(initialTitle)
  const [content, setContent] = useState(initialContent)
  const [markdownGuideOpen, setMarkdownGuideOpen] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      toast.error('Укажите заголовок')
      return
    }
    onSubmit({ title: title.trim(), content })
  }

  return (
    <form className="kb-article-form" onSubmit={handleSubmit}>
      <label className="form-label">
        Заголовок
        <input className="form-control" value={title} onChange={(e) => setTitle(e.target.value)} required />
      </label>

      <div className="kb-editor-wrapper">
        <button
          type="button"
          className="kb-markdown-guide-toggle"
          onClick={() => setMarkdownGuideOpen(true)}
          title="Показать/скрыть гайд по Markdown"
        >
          📚 Гайд по Markdown
        </button>
        <div className="kb-editor-split">
          <div className="kb-editor-pane">
            <h3 className="kb-editor-pane-title">Markdown</h3>
            <textarea
              className="form-control kb-editor-textarea"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Текст в формате Markdown…"
              rows={24}
            />
          </div>
          <div className="kb-editor-pane">
            <h3 className="kb-editor-pane-title">Предпросмотр</h3>
            <MarkdownLivePreview markdown={content} className="kb-editor-preview-box" />
          </div>
        </div>
      </div>

      <MarkdownGuideSidebar open={markdownGuideOpen} onClose={() => setMarkdownGuideOpen(false)} />

      <div className="kb-form-actions">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => (mode === 'create' ? navigate(`/knowledge-base?section=${encodeURIComponent(sectionId)}`) : navigate(kbArticlePath(sectionId, filename)))}
          disabled={pending}
        >
          Отмена
        </button>
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {mode === 'create' ? 'Создать' : 'Сохранить'}
        </button>
      </div>
    </form>
  )
}

export default KnowledgeBaseArticleFormFields
