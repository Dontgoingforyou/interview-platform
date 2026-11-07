import { MANAGER_METRICS_MAIN, MANAGER_METRIC_TOOLTIP_KEYS } from '../../../constants/managerMetrics'
import type { ManagersAnalytics } from '../../../types/managerDashboard'
import { formatManagerMetricValue, numericManagerMetricValue } from '../../../utils/managers/managerMetricsDisplay'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface ManagersMetricsMainGridProps {
  analytics: ManagersAnalytics
}

/** Сетка KPI дашборда менеджеров */
function ManagersMetricsMainGrid({ analytics }: ManagersMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Метрики команды" gridClassName="metrics-grid metrics-loaded managers-metrics-grid" collapsibleOnMobile>
      {MANAGER_METRICS_MAIN.map((m) => {
        const mainVal = formatManagerMetricValue(analytics, String(m.key), m.format)
        const sub =
          m.subtitleKey != null && m.subtitleTemplate === 'interviewsPeriod'
            ? `(${String(analytics[m.subtitleKey] ?? 0)} интервью за период)`
            : null
        const ttKey = MANAGER_METRIC_TOOLTIP_KEYS[String(m.key)] ?? String(m.key)
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const isTopSpeed = String(m.key) === 'top-speed'
        const numericTarget = isTopSpeed
          ? null
          : numericManagerMetricValue(analytics, String(m.key), m.format)
        return (
          <MetricCard key={String(m.key)} label={m.label} tooltip={tt || undefined} light={m.light} subtitle={sub}>
            <MetricAnimatedStrong
              key={`mm-${String(m.key)}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericTarget}
              format={m.format === 'decimal2' ? 'decimal2' : undefined}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default ManagersMetricsMainGrid
