import { useState, type ReactNode } from 'react'

interface ManagersChartCollapsibleBlockProps {
  title: string
  /** Уникальный id на странице (для aria-controls и id панели) */
  panelId: string
  children: ReactNode
}

/**
 * Карточка графика менеджеров: заголовок + кнопка сворачивания, плавное скрытие тела.
 */
function ManagersChartCollapsibleBlock({ title, panelId, children }: ManagersChartCollapsibleBlockProps) {
  const contentId = `managers-chart-panel-${panelId}`
  const [expanded, setExpanded] = useState(true)

  return (
    <div className={`managers-chart-block${expanded ? '' : ' is-chart-collapsed'}`}>
      <div className="managers-chart-head">
        <h3 className="managers-chart-title">{title}</h3>
        <button
          type="button"
          className="managers-chart-toggle"
          aria-expanded={expanded}
          aria-controls={contentId}
          aria-label={expanded ? 'Свернуть график' : 'Развернуть график'}
          onClick={() => setExpanded((v) => !v)}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
      </div>
      <div className={`managers-chart-panel-collapse${expanded ? '' : ' is-collapsed'}`}>
        <div className="managers-chart-panel-collapse__inner" id={contentId}>
          {children}
        </div>
      </div>
    </div>
  )
}

export default ManagersChartCollapsibleBlock
