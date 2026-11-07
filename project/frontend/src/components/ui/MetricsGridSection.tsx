import { useId, useState } from 'react'
import type { ReactNode } from 'react'

import { useMediaQuery } from '../../hooks/useMediaQuery'
import CollapsibleSection from './CollapsibleSection'

const DEFAULT_TITLE_CLASS = 'interviews-section-title interviews-metrics-static-heading'
const DEFAULT_GRID_CLASS = 'metrics-grid metrics-loaded'

interface MetricsGridSectionProps {
  /** Если задан — рендерится h2 над сеткой. */
  title?: string
  titleClassName?: string
  titleEnd?: ReactNode
  /** Классы на контейнере сетки. */
  gridClassName?: string
  /**
   * На мобильных (≤768px) оборачивает блок в CollapsibleSection,
   * позволяя скрыть метрики для экономии места.
   * Требует наличия title.
   */
  collapsibleOnMobile?: boolean
  children: ReactNode
}

/** Заголовок секции + контейнер сетки метрик. */
function MetricsGridSection({
  title,
  titleClassName = DEFAULT_TITLE_CLASS,
  titleEnd,
  gridClassName = DEFAULT_GRID_CLASS,
  collapsibleOnMobile = false,
  children,
}: MetricsGridSectionProps) {
  const sectionId = useId()
  const isMobile = useMediaQuery('(max-width: 768px)')
  const [expanded, setExpanded] = useState(() => !isMobile)

  const grid = <div className={gridClassName}>{children}</div>

  if (collapsibleOnMobile && isMobile && title) {
    return (
      <CollapsibleSection
        sectionId={sectionId}
        expanded={expanded}
        onExpandedChange={setExpanded}
        title={title}
        headerTrailing={titleEnd}
      >
        {grid}
      </CollapsibleSection>
    )
  }

  return (
    <>
      {title ? (
        <div className="metrics-grid-section__title-row">
          <h2 className={titleClassName}>{title}</h2>
          {titleEnd ? <div className="metrics-grid-section__title-end">{titleEnd}</div> : null}
        </div>
      ) : null}
      {grid}
    </>
  )
}

export default MetricsGridSection
