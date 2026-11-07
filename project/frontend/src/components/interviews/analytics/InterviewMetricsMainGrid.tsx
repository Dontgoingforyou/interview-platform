import { METRICS_MAIN, MAIN_METRIC_TOOLTIP_KEYS } from '../../../constants/interviewMetrics'
import { formatMetricValue, numericMetricValue } from '../../../utils/interviews/interviewMetricsDisplay'
import type { InterviewAnalytics } from '../../../types/interview'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface InterviewMetricsMainGridProps {
  analytics: InterviewAnalytics
}

/** Ключевые метрики за 30 дней (сетка карточек). */
function InterviewMetricsMainGrid({ analytics }: InterviewMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Ключевые метрики" collapsibleOnMobile>
      {METRICS_MAIN.map((m) => {
        const raw = analytics
        const mainVal = formatMetricValue(raw, m.key, m.format)
        const sub =
          m.subtitleKey && raw[m.subtitleKey] != null
            ? `(${String(raw[m.subtitleKey])} интервью за 30 дней)`
            : null
        const ttKey = MAIN_METRIC_TOOLTIP_KEYS[String(m.key)] ?? String(m.key).replace(/_/g, '-')
        const tt = analytics.tooltips?.[ttKey] ?? ''
        return (
          <MetricCard key={m.key} label={m.label} tooltip={tt || undefined} light={m.light} subtitle={sub}>
            <MetricAnimatedStrong
              key={`m-${String(m.key)}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericMetricValue(raw, m.key)}
              format={m.format}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default InterviewMetricsMainGrid
