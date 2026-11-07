import { OFFER_METRICS_MAIN, OFFER_METRIC_TOOLTIP_KEYS } from '../../../constants/offerMetrics'
import {
  formatOfferMetricValue,
  numericOfferMetricValue,
} from '../../../utils/offers/offerMetricsDisplay'
import type { OfferAnalytics } from '../../../types/offer'
import { MetricAnimatedStrong } from '../../ui/MetricAnimatedStrong'
import MetricCard from '../../ui/MetricCard'
import MetricsGridSection from '../../ui/MetricsGridSection'

interface OfferMetricsMainGridProps {
  analytics: OfferAnalytics
}

/** Сетка карточек аналитики офферов */
function OfferMetricsMainGrid({ analytics }: OfferMetricsMainGridProps) {
  return (
    <MetricsGridSection title="Аналитика трудоустройств" collapsibleOnMobile>
      {OFFER_METRICS_MAIN.map((m) => {
        const mainVal = formatOfferMetricValue(analytics, String(m.key), m.format)
        const ttKey = OFFER_METRIC_TOOLTIP_KEYS[String(m.key)] ?? String(m.key)
        const tt = analytics.tooltips?.[ttKey] ?? ''
        const animFormat = m.format === 'currency' ? 'integerRuble' : undefined
        return (
          <MetricCard key={String(m.key)} label={m.label} tooltip={tt || undefined} light={m.light}>
            <MetricAnimatedStrong
              key={`om-${String(m.key)}-${mainVal}`}
              formatted={mainVal}
              numericTarget={numericOfferMetricValue(analytics, String(m.key), m.format)}
              format={animFormat}
            />
          </MetricCard>
        )
      })}
    </MetricsGridSection>
  )
}

export default OfferMetricsMainGrid
