import { CollapsibleSection } from '../../ui'
import type { InterviewTypeBreakdown } from '../../../types/interview'

interface InterviewTypeStatsSectionProps {
  sectionId: string
  expanded: boolean
  onExpandedChange: (v: boolean) => void
  data: InterviewTypeBreakdown
}

/** Сводка по типам интервью за выбранные даты (чипы + полосы). */
function InterviewTypeStatsSection({
  sectionId,
  expanded,
  onExpandedChange,
  data,
}: InterviewTypeStatsSectionProps) {
  const total = data.total
  return (
    <CollapsibleSection
      sectionId={sectionId}
      expanded={expanded}
      onExpandedChange={onExpandedChange}
      title="Статистика собеседований по выбранным датам"
      headingLevel={3}
      className="interviews-subsection--type-stats"
    >
      <div className="interview-type-stats interview-type-stats--embedded">
        <ul className="stats-chips" role="list">
          <li className="stats-chip stats-chip--total" role="listitem">
            <span className="stats-chip-label">Всего</span>
            <strong className="stats-chip-value">{total}</strong>
          </li>
          {data.items.map((item) => {
            const pct = total > 0 ? Math.round((item.count / total) * 1000) / 10 : 0
            const pctWidth = total > 0 ? (item.count / total) * 100 : 0
            return (
              <li key={item.type} className="stats-chip" role="listitem">
                <div className="stats-chip-bar-track" aria-hidden>
                  <div className="stats-chip-bar-fill" style={{ width: `${pctWidth}%` }} />
                </div>
                <span className="stats-chip-label">{item.label}</span>
                <strong className="stats-chip-value">{item.count}</strong>
                <span className="stats-chip-pct">{pct}%</span>
              </li>
            )
          })}
        </ul>
      </div>
    </CollapsibleSection>
  )
}

export default InterviewTypeStatsSection
