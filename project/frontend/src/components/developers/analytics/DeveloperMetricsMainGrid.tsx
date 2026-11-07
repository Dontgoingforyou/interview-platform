import type { ReactNode } from 'react'

import { DEVELOPER_METRICS_MAIN, DEVELOPER_METRIC_TOOLTIP_KEYS } from '../../../constants/developerMetrics'
import {
  formatDeveloperMetricValue,
  numericDeveloperMetricValue,
} from '../../../utils/developers/developerMetricsDisplay'
import type { DeveloperAnalytics } from '../../../types/developer'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface DeveloperMetricsMainGridProps {
  analytics: DeveloperAnalytics
  titleEnd?: ReactNode
}

function subtitleForMetric(
  analytics: DeveloperAnalytics,
  subtitleKey: string | undefined,
  suffix: string | undefined,
): string {
  if (!subtitleKey || !suffix) {
    return ''
  }
  const raw = analytics[subtitleKey as keyof DeveloperAnalytics]
  if (raw === null || raw === undefined) {
    return ''
  }
  return `${raw}${suffix}`
}

/** Сетка карточек аналитики разработчиков */
function DeveloperMetricsMainGrid({ analytics, titleEnd }: DeveloperMetricsMainGridProps) {
  return (
    <MetricsGridSection
      title="Ключевые метрики"
      titleEnd={titleEnd}
      gridClassName="metrics-grid metrics-loaded developers-metrics-grid"
      collapsibleOnMobile
    >
      {DEVELOPER_METRICS_MAIN.map((m) => {
        const mainVal = formatDeveloperMetricValue(analytics, m.key, m.format)
        const ttKey = DEVELOPER_METRIC_TOOLTIP_KEYS[m.key] ?? m.key
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const animFormat = m.format === 'currency' ? 'integerRuble' : undefined
        const sub = subtitleForMetric(analytics, m.subtitleKey, m.subtitleSuffix)
        return (
          <MetricCard
            key={m.key}
            label={m.label}
            tooltip={tt || undefined}
            light={m.light}
            subtitle={sub || undefined}
            subtitleVariant="subtitleDiv"
          >
            <MetricAnimatedStrong
              key={`dm-${m.key}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericDeveloperMetricValue(analytics, m.key, m.format)}
              format={animFormat}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default DeveloperMetricsMainGrid
