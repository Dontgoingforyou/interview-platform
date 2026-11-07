import {
  DIRECTION_METRICS_MAIN,
  DIRECTION_METRIC_TOOLTIP_KEYS,
} from '../../../constants/directionMetrics'
import type { DirectionMetricsResponse } from '../../../types/direction'
import {
  formatDirectionMetricValue,
  numericDirectionMetricValue,
} from '../../../utils/directions/directionMetricsDisplay'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface DirectionMetricsMainGridProps {
  analytics: DirectionMetricsResponse
}

function subtitleForMetric(
  analytics: DirectionMetricsResponse,
  subtitleKey: string | undefined,
): string {
  if (!subtitleKey) {
    return ''
  }
  const raw = (analytics as unknown as Record<string, unknown>)[subtitleKey]
  if (raw === null || raw === undefined) {
    return ''
  }
  return String(raw)
}

/** Сетка карточек метрик по направлениям */
function DirectionMetricsMainGrid({ analytics }: DirectionMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Ключевые метрики" gridClassName="metrics-grid metrics-loaded directions-metrics-grid" collapsibleOnMobile>
      {DIRECTION_METRICS_MAIN.map((m) => {
        const mainVal = formatDirectionMetricValue(analytics, m.dataKey, m.format)
        const ttKey = DIRECTION_METRIC_TOOLTIP_KEYS[m.metricKey] ?? m.metricKey
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const numericTarget = numericDirectionMetricValue(analytics, m.dataKey, m.format)
        const animFormat = m.format === 'percent' ? 'percent' : undefined
        const sub = subtitleForMetric(analytics, m.subtitleDataKey)
        return (
          <MetricCard
            key={m.metricKey}
            label={m.label}
            tooltip={tt || undefined}
            dataMetric={m.metricKey}
            subtitle={sub || undefined}
            subtitleVariant="subtitleDiv"
          >
            <MetricAnimatedStrong
              key={`dm-${m.metricKey}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericTarget}
              format={animFormat}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default DirectionMetricsMainGrid
