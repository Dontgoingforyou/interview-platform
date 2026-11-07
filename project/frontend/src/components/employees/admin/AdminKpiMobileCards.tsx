import type { AdminKpiResponse, AdminKpiRow } from '../../../types/employee'

interface AdminKpiMobileCardsProps {
  data: AdminKpiResponse
  openRows: Set<number>
  onToggleRow: (index: number) => void
}

function AdminKpiCard({
  item,
  idx,
  minKpi,
  isOpen,
  onToggle,
}: {
  item: AdminKpiRow
  idx: number
  minKpi: number
  isOpen: boolean
  onToggle: () => void
}) {
  return (
    <article className="admin-mobile-card">
      <div className="admin-mobile-card__head">
        <div className="admin-mobile-card__meta">
          <span className="admin-mobile-card__num">{idx + 1}.</span>
          <strong className="admin-mobile-card__name">{item.manager.full_name}</strong>
        </div>
        <div className="admin-mobile-card__badges">
          <span className="kpi-badge">{item.qualifying_weeks_count}</span>
          <span className="admin-mobile-card__label">нед. ≥ {minKpi}</span>
        </div>
      </div>

      <dl className="admin-mobile-card__dl">
        <div>
          <dt>Активных разработчиков</dt>
          <dd>{item.total_active_devs}</dd>
        </div>
      </dl>

      {item.qualifying_weeks.length > 0 ? (
        <button
          type="button"
          className="admin-mobile-card__toggle"
          onClick={onToggle}
          aria-expanded={isOpen}
        >
          Детали по неделям {isOpen ? '▾' : '▸'}
        </button>
      ) : null}

      {isOpen && item.qualifying_weeks.length > 0 ? (
        <div className="admin-mobile-card__details">
          {item.qualifying_weeks.map((w) => (
            <div key={`${w.week_start}-${w.week_end}`} className="kpi-week-item">
              <div className="kpi-week-item__period">
                {w.week_start} — {w.week_end}
              </div>
              <dl className="kpi-week-item__dl">
                <div>
                  <dt>KPI</dt>
                  <dd>
                    <strong className="text-accent-green">{w.kpi}</strong>
                  </dd>
                </div>
                <div>
                  <dt>Собесов</dt>
                  <dd>{w.total_interviews}</dd>
                </div>
                <div>
                  <dt>Разработчиков</dt>
                  <dd>{w.active_count}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  )
}

export default function AdminKpiMobileCards({ data, openRows, onToggleRow }: AdminKpiMobileCardsProps) {
  return (
    <ul className="admin-kpi-mobile-cards" aria-label="KPI менеджеров">
      {data.results.map((item, idx) => (
        <li key={item.manager.email}>
          <AdminKpiCard
            item={item}
            idx={idx}
            minKpi={data.min_kpi}
            isOpen={openRows.has(idx)}
            onToggle={() => onToggleRow(idx)}
          />
        </li>
      ))}
    </ul>
  )
}
