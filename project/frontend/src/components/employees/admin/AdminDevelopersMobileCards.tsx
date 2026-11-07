import type { AdminDeveloperRow, AdminDevelopersResponse } from '../../../types/employee'
import AdminDevelopersInternList from './AdminDevelopersInternList'

interface AdminDevelopersMobileCardsProps {
  data: AdminDevelopersResponse
  openRows: Set<number>
  onToggleListRow: (index: number) => void
  isTogglePending: boolean
  onSetManagerActive: (email: string, isActive: boolean) => void
  isHiddenSection?: boolean
}

function AdminDeveloperCard({
  item,
  idx,
  isOpen,
  onToggle,
  isTogglePending,
  onSetManagerActive,
  isHiddenSection,
}: {
  item: AdminDeveloperRow
  idx: number
  isOpen: boolean
  onToggle: () => void
  isTogglePending: boolean
  onSetManagerActive: (email: string, isActive: boolean) => void
  isHiddenSection: boolean
}) {
  return (
    <article className={`admin-mobile-card${item.active_count === 0 ? ' admin-mobile-card--empty' : ''}`}>
      <div className="admin-mobile-card__head">
        <div className="admin-mobile-card__meta">
          <span className="admin-mobile-card__num">{idx + 1}.</span>
          <strong className={`admin-mobile-card__name${item.active_count === 0 ? ' text-muted-inline' : ''}`}>
            {item.manager.full_name}
          </strong>
          {isHiddenSection ? (
            <span className="admin-mobile-card__email text-muted-inline">
              {item.manager.email}
            </span>
          ) : null}
        </div>
        {item.active_count > 0 ? (
          <span className="dev-count-badge">{item.active_count}</span>
        ) : (
          <span className="text-muted-inline admin-mobile-card__empty-badge">—</span>
        )}
      </div>

      <div className="admin-mobile-card__actions">
        {item.active_count > 0 ? (
          <button
            type="button"
            className="admin-mobile-card__toggle"
            onClick={onToggle}
            aria-expanded={isOpen}
            style={{ marginBottom: 0 }}
          >
            Список разработчиков {isOpen ? '▾' : '▸'}
          </button>
        ) : null}
        {!isHiddenSection ? (
          <button
            type="button"
            className="btn-hide-manager"
            title="Скрыть менеджера из списков"
            disabled={isTogglePending}
            onClick={() => {
              if (window.confirm(`Скрыть менеджера «${item.manager.full_name}» из списков?`)) {
                onSetManagerActive(item.manager.email, false)
              }
            }}
          >
            ✕ Скрыть
          </button>
        ) : (
          <button
            type="button"
            className="btn-restore-manager"
            title="Восстановить менеджера"
            disabled={isTogglePending}
            onClick={() => onSetManagerActive(item.manager.email, true)}
          >
            ↩ Восстановить
          </button>
        )}
      </div>

      {isOpen && item.active_count > 0 ? (
        <div className="admin-mobile-card__intern-list">
          <AdminDevelopersInternList interns={item.interns} />
        </div>
      ) : null}
    </article>
  )
}

export default function AdminDevelopersMobileCards({
  data,
  openRows,
  onToggleListRow,
  isTogglePending,
  onSetManagerActive,
  isHiddenSection = false,
}: AdminDevelopersMobileCardsProps) {
  const items = isHiddenSection ? data.hidden_results : data.results

  return (
    <ul className="admin-developers-mobile-cards" aria-label={isHiddenSection ? 'Скрытые менеджеры' : 'Менеджеры'}>
      {items.map((item, idx) => (
        <li key={item.manager.email}>
          <AdminDeveloperCard
            item={item}
            idx={idx}
            isOpen={openRows.has(idx)}
            onToggle={() => onToggleListRow(idx)}
            isTogglePending={isTogglePending}
            onSetManagerActive={onSetManagerActive}
            isHiddenSection={isHiddenSection}
          />
        </li>
      ))}
    </ul>
  )
}
