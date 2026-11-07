import type { ManagersDashboardTableRow } from '../../../types/managerDashboard'
import { formatRuDate } from '../../../utils/dateFormat'

interface ManagerListMobileCardsProps {
  rows: ManagersDashboardTableRow[]
}

function ManagerListMobileCards({ rows }: ManagerListMobileCardsProps) {
  return (
    <ul className="managers-mobile-cards">
      {rows.map((row) => (
        <li key={row.email} className="managers-mobile-card">
          <div className="managers-mobile-card__title">{row.full_name || '—'}</div>
          <dl className="managers-mobile-card__stats">
            <div>
              <dt>Всего</dt>
              <dd>{row.candidates_count}</dd>
            </div>
            <div>
              <dt>Горячие</dt>
              <dd>{row.hot_candidates_count}</dd>
            </div>
            <div>
              <dt>В работе</dt>
              <dd>{row.active_candidates_count}</dd>
            </div>
            <div>
              <dt>В портфеле</dt>
              <dd>{row.portfolio_candidates_count}</dd>
            </div>
            <div>
              <dt>Интервью</dt>
              <dd>{row.interviews_count}</dd>
            </div>
            <div>
              <dt>Успешные</dt>
              <dd>{row.successful_candidates_count}</dd>
            </div>
            <div className="managers-mobile-card__full">
              <dt>Направления</dt>
              <dd>{row.directions || '—'}</dd>
            </div>
            <div>
              <dt>Последнее интервью</dt>
              <dd>{formatRuDate(row.last_interview_date)}</dd>
            </div>
          </dl>
        </li>
      ))}
    </ul>
  )
}

export default ManagerListMobileCards
