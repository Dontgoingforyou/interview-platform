import type { ReactNode } from 'react'

import MetricInfoIcon from './MetricInfoIcon'

export type MetricCardSubtitleVariant = 'mutedSpan' | 'subtitleDiv'

interface MetricCardProps {
  label: string
  tooltip?: string
  light?: boolean
  dataMetric?: string
  className?: string
  subtitle?: ReactNode
  /** Разметка подписи под значением: span.muted или div.metric-subtitle. */
  subtitleVariant?: MetricCardSubtitleVariant
  children: ReactNode
}

/** Карточка метрики аналитики: заголовок, опциональный тултип, слот значения, подпись. */
function MetricCard({
  label,
  tooltip,
  light,
  dataMetric,
  className = '',
  subtitle,
  subtitleVariant = 'mutedSpan',
  children,
}: MetricCardProps) {
  const cardClass = ['metric-card', light ? 'light' : '', className].filter(Boolean).join(' ')
  return (
    <div className={cardClass} data-metric={dataMetric}>
      <div className="metric-header">
        <small>{label}</small>
        {tooltip ? <MetricInfoIcon text={tooltip} /> : null}
      </div>
      {children}
      {subtitle ? (
        subtitleVariant === 'subtitleDiv' ? (
          <div className="metric-subtitle text-muted">{subtitle}</div>
        ) : (
          <span className="muted">{subtitle}</span>
        )
      ) : null}
    </div>
  )
}

export default MetricCard
