import { Link } from 'react-router-dom'

interface Crumb {
  label: string
  to?: string
}

interface KnowledgeBaseBreadcrumbsProps {
  items: Crumb[]
}

/**
 * Хлебные крошки для раздела базы знаний.
 */
function KnowledgeBaseBreadcrumbs({ items }: KnowledgeBaseBreadcrumbsProps) {
  return (
    <nav className="kb-breadcrumbs" aria-label="Навигация">
      <ol className="kb-breadcrumbs-list">
        {items.map((item, i) => (
          <li key={`${item.label}-${i}`} className="kb-breadcrumbs-item">
            {i > 0 && <span className="kb-breadcrumbs-sep">/</span>}
            {item.to ? (
              <Link to={item.to} className="kb-breadcrumbs-link">
                {item.label}
              </Link>
            ) : (
              <span className="kb-breadcrumbs-current">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export default KnowledgeBaseBreadcrumbs
