import { CollapsibleSection } from '../../ui'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import { ALL_TIME_TOOLTIP_KEYS, METRICS_ALL_TIME } from '../../../constants/interviewMetrics'
import { formatMetricValue, numericMetricValue } from '../../../utils/interviews/interviewMetricsDisplay'
import type { InterviewAnalytics } from '../../../types/interview'

interface InterviewAllTimeMetricsSectionProps {
  sectionId: string
  expanded: boolean
  onExpandedChange: (v: boolean) => void
  analytics: InterviewAnalytics
}

/** Сворачиваемый блок «Статистика за всё время». */
function InterviewAllTimeMetricsSection({
  sectionId,
  expanded,
  onExpandedChange,
  analytics,
}: InterviewAllTimeMetricsSectionProps) {
  return (
    <CollapsibleSection
      sectionId={sectionId}
      expanded={expanded}
      onExpandedChange={onExpandedChange}
      title="Статистика за все время"
    >
      <div className="metrics-grid metrics-loaded">
        {METRICS_ALL_TIME.map((m) => {
          const v = formatMetricValue(analytics, m.dataKey, m.format)
          const sub =
            m.subtitleKey && analytics[m.subtitleKey] != null
              ? `(${String(analytics[m.subtitleKey])} интервью)`
              : null
          const ttKey = ALL_TIME_TOOLTIP_KEYS[m.dataKey]
          const tt = ttKey ? analytics.tooltips?.[ttKey] ?? '' : ''
          return (
            <MetricCard key={m.dataKey} label={m.label} tooltip={tt || undefined} light={m.light} subtitle={sub}>
              <MetricAnimatedStrong
                key={`a-${m.dataKey}-${v}`}
                formatted={v}
                numericTarget={numericMetricValue(analytics, m.dataKey)}
                format={m.format}
              />
            </MetricCard>
          )
        })}
      </div>
    </CollapsibleSection>
  )
}

export default InterviewAllTimeMetricsSection
