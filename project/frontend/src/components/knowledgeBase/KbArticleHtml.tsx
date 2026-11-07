interface KbArticleHtmlProps {
  html: string
  className?: string
}

/**
 * HTML статьи, подготовленный на сервере (bleach). Не подставлять пользовательский HTML из редактора.
 */
function KbArticleHtml({ html, className = '' }: KbArticleHtmlProps) {
  return (
    <div
      className={`kb-article-html kb-markdown-preview ${className}`.trim()}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export default KbArticleHtml
