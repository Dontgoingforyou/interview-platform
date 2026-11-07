import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

interface MarkdownLivePreviewProps {
  markdown: string
  /** Дополнительный класс для контейнера превью */
  className?: string
}

/**
 * Живой превью Markdown в редакторе (санитизация на клиенте).
 */
function MarkdownLivePreview({ markdown, className = '' }: MarkdownLivePreviewProps) {
  return (
    <div className={`kb-markdown-preview ${className}`.trim()}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
        {markdown || '*Пустой документ*'}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownLivePreview
