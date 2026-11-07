import { DEBT_METRICS_MAIN, DEBT_METRIC_TOOLTIP_KEYS } from '../../../constants/debtMetrics'
import { formatDebtMetricValue, numericDebtMetricValue } from '../../../utils/debts/debtMetricsDisplay'
import type { DebtAnalytics } from '../../../types/debt'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface DebtMetricsMainGridProps {
  analytics: DebtAnalytics
}

/** Сетка карточек аналитики долгов */
function DebtMetricsMainGrid({ analytics }: DebtMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Аналитика долгов отдела" collapsibleOnMobile>
      {DEBT_METRICS_MAIN.map((m) => {
        const mainVal = formatDebtMetricValue(analytics, String(m.key), m.format)
        const sub =
          m.subtitleKey && analytics[m.subtitleKey] != null && String(analytics[m.subtitleKey]).trim() !== ''
            ? `(${String(analytics[m.subtitleKey])})`
            : null
        const ttKey = DEBT_METRIC_TOOLTIP_KEYS[String(m.key)] ?? String(m.key)
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const animFormat =
          m.format === 'percent'
            ? 'percent'
            : m.format === 'currency'
              ? 'integerRuble'
              : undefined
        return (
          <MetricCard key={String(m.key)} label={m.label} tooltip={tt || undefined} light={m.light} subtitle={sub}>
            <MetricAnimatedStrong
              key={`dm-${String(m.key)}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericDebtMetricValue(analytics, String(m.key), m.format)}
              format={animFormat}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default DebtMetricsMainGrid
