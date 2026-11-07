import type { ReactNode } from 'react'

/** Секция с заголовком и сворачиваемым контентом (как блок «Поиск и фильтры» на странице собеседований). */
function CollapsibleSection({
  sectionId,
  expanded,
  onExpandedChange,
  title,
  headingLevel = 2,
  headingId,
  headerTrailing,
  children,
  className,
}: {
  sectionId: string
  expanded: boolean
  onExpandedChange: (next: boolean) => void
  title: ReactNode
  headingLevel?: 2 | 3
  headingId?: string
  /** Между заголовком и кнопкой сворачивания (клики не переключают секцию). */
  headerTrailing?: ReactNode
  children: ReactNode
  className?: string
}) {
  const H = headingLevel === 2 ? 'h2' : 'h3'
  return (
    <div className={`interviews-subsection${className ? ` ${className}` : ''}`}>
      <div className="interviews-subsection-card">
        <div
          className="interviews-subsection-head"
          onClick={() => onExpandedChange(!expanded)}
          role="presentation"
        >
          <H className="interviews-section-title" id={headingId}>
            {title}
          </H>
          {headerTrailing ? (
            <div
              className="interviews-subsection-head-trailing"
              role="presentation"
              onClick={(e) => e.stopPropagation()}
              onKeyDown={(e) => e.stopPropagation()}
            >
              {headerTrailing}
            </div>
          ) : null}
          <button
            type="button"
            className="interviews-subsection-toggle"
            aria-expanded={expanded}
            aria-controls={sectionId}
            aria-label={expanded ? 'Свернуть секцию' : 'Развернуть секцию'}
            onClick={(e) => {
              e.stopPropagation()
              onExpandedChange(!expanded)
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              aria-hidden
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
        </div>
        <div className={`interviews-collapsible-block${expanded ? '' : ' is-collapsed'}`}>
          <div className="interviews-collapsible-block__inner" id={sectionId}>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CollapsibleSection
