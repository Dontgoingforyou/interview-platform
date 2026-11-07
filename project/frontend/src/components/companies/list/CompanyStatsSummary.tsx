import type { CompanyStats } from '../../../types/company'

type Props = {
  stats: CompanyStats
}

/**
 * Блок чисел над таблицей.
 */
function CompanyStatsSummary({ stats }: Props) {
  return (
    <div className="company-stats-summary">
      <div className="stats-summary">
        <span className="stats-total">
          Всего компаний: <strong>{stats.total_count}</strong>
        </span>
        <span className="stats-separator">|</span>
        <span className="stats-item">
          <span className="stats-label">С собеседованиями:</span>{' '}
          <strong>{stats.with_interviews_count}</strong>
        </span>
        <span className="stats-separator">|</span>
        <span className="stats-item">
          <span className="stats-label">Без собеседований:</span>{' '}
          <strong>{stats.without_interviews_count}</strong>
        </span>
        {stats.bigtech_count > 0 ? (
          <>
            <span className="stats-separator">|</span>
            <span className="stats-item">
              <span className="stats-label">Бигтехов:</span> <strong>{stats.bigtech_count}</strong>
            </span>
          </>
        ) : null}
      </div>
    </div>
  )
}

export default CompanyStatsSummary
