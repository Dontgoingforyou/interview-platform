import { SAD_INTERN_METRICS_MAIN, SAD_INTERN_METRIC_TOOLTIP_KEYS } from '../../../constants/sadInternMetrics'
import type { SadInternAnalytics } from '../../../types/sadIntern'
import {
  formatSadInternMetricDisplay,
  numericSadInternMetric,
} from '../../../utils/sadIntern/sadInternMetricsDisplay'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface SadInternMetricsMainGridProps {
  analytics: SadInternAnalytics
}

/** Сетка карточек аналитики «грустят». */
function SadInternMetricsMainGrid({ analytics }: SadInternMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Аналитика списка ожидания" gridClassName="metrics-grid metrics-loaded sad-intern-metrics-grid" collapsibleOnMobile>
      {SAD_INTERN_METRICS_MAIN.map((m) => {
        const mainVal = formatSadInternMetricDisplay(analytics, String(m.key), m.format)
        const subKey = 'subtitleKey' in m ? m.subtitleKey : undefined
        const sub =
          subKey && analytics[subKey] != null && String(analytics[subKey]).trim() !== ''
            ? `(${String(analytics[subKey])})`
            : null
        const ttKey = SAD_INTERN_METRIC_TOOLTIP_KEYS[String(m.key)] ?? String(m.key)
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const numericTarget = numericSadInternMetric(analytics, String(m.key))
        const light = 'light' in m && m.light
        return (
          <MetricCard key={String(m.key)} label={m.label} tooltip={tt || undefined} light={light} subtitle={sub}>
            <MetricAnimatedStrong
              key={`si-${String(m.key)}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericTarget}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default SadInternMetricsMainGrid
