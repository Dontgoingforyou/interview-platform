import type { DirectionMetricRow } from '../../../types/direction'

function formatTableDate(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (m) {
    return `${m[3]}.${m[2]}.${m[1]}`
  }
  return iso
}

interface DirectionMetricsMobileCardsProps {
  rows: DirectionMetricRow[]
}

/** Карточки строк таблицы метрик на узких экранах. */
function DirectionMetricsMobileCards({ rows }: DirectionMetricsMobileCardsProps) {
  return (
    <ul className="directions-mobile-cards">
      {rows.map((metric) => (
        <li key={metric.direction.id} className="directions-mobile-card">
          <div className="directions-mobile-card__title">{metric.direction.name ?? '—'}</div>
          <dl className="directions-mobile-card__stats">
            <div>
              <dt>Интервью</dt>
              <dd>{metric.interviews}</dd>
            </div>
            <div>
              <dt>Тех интервью</dt>
              <dd>{metric.tech_interviews}</dd>
            </div>
            <div>
              <dt>Кандидатов</dt>
              <dd>{metric.candidates}</dd>
            </div>
            <div>
              <dt>Конверсия</dt>
              <dd>{metric.conversion_rate}%</dd>
            </div>
            <div>
              <dt>Предстоящие</dt>
              <dd>{metric.upcoming_interviews}</dd>
            </div>
            <div>
              <dt>Последнее интервью</dt>
              <dd>{formatTableDate(metric.last_interview_date)}</dd>
            </div>
          </dl>
        </li>
      ))}
    </ul>
  )
}

export default DirectionMetricsMobileCards
