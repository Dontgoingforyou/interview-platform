import type { DeveloperStatRow } from '../../../types/developer'

function formatActivity(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const d = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(d.getTime())) {
    return iso
  }
  return d.toLocaleDateString('ru-RU')
}

interface DeveloperListMobileCardsProps {
  results: DeveloperStatRow[]
}

function DeveloperListMobileCards({ results }: DeveloperListMobileCardsProps) {
  return (
    <ul className="developers-mobile-cards">
      {results.map((row) => (
        <li key={`${row.intern_id}-${row.direction_id ?? 'x'}`} className="developers-mobile-card">
          <div className="developers-mobile-card__title">{row.intern_name}</div>
          <dl className="developers-mobile-card__stats">
            <div>
              <dt>Направление</dt>
              <dd>{row.direction_name ?? '—'}</dd>
            </div>
            <div>
              <dt>Последняя активность</dt>
              <dd>{formatActivity(row.last_interview_date)}</dd>
            </div>
            <div>
              <dt>Интервью</dt>
              <dd>{row.interview_count}</dd>
            </div>
          </dl>
        </li>
      ))}
    </ul>
  )
}

export default DeveloperListMobileCards
