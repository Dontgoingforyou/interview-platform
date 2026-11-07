import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import Pagination from '../../Pagination'
import TableScroll from '../../ui/TableScroll'
import SadInternListMobileCards from './SadInternListMobileCards'
import SadInternListTableHead from './SadInternListTableHead'
import type { SadInternGroupedGroup, SadInternListFilters, SadInternListItem } from '../../../types/sadIntern'
import { formatRuDate } from '../../../utils/dateFormat'
import { telegramHref } from '../../../utils/debts/debtTableDisplay'

function rowStatusClass(status: string | null): string {
  if (status === 'rejected' || status === 'fired') {
    return 'status-negative'
  }
  if (status === 'accepted') {
    return 'status-positive'
  }
  return ''
}

interface SadInternGroupSectionProps {
  group: SadInternGroupedGroup
  filters: SadInternListFilters
  groupPages: Record<string, number>
  onGroupPageChange: (key: string, page: number) => void
  onToggleSort: (field: string) => void
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

/** Одно направление: заголовок, таблица, пагинация внутри группы. */
function SadInternGroupSection({
  group,
  filters,
  groupPages,
  onGroupPageChange,
  onToggleSort,
  canWrite,
  isAdmin,
  onDelete,
}: SadInternGroupSectionProps) {
  const sectionId =
    group.direction_id == null ? 'direction-none' : `direction-${group.direction_id}`

  const currentPage = groupPages[group.pagination_key] ?? group.page

  return (
    <section className="sad-intern-direction-section" id={sectionId} aria-labelledby={`${sectionId}-title`}>
      <h3 id={`${sectionId}-title`} className="sad-intern-direction-title">
        {group.direction_name}
      </h3>
      <div className="sad-intern-table-desktop">
        <TableScroll className="table-scroll--plain">
          <table className={`data-table sad-intern-table ${DATA_TABLE_STICKY_LEADING}`}>
            <SadInternListTableHead filters={filters} onToggleSort={onToggleSort} canWrite={canWrite} />
            <tbody>
              {group.results.map((row: SadInternListItem) => {
                const tgUrl = telegramHref(row.telegram_username ?? '')
                return (
                  <tr key={row.id} className={rowStatusClass(row.status)}>
                    <td>{row.id}</td>
                    <td>{row.intern_name}</td>
                    <td>{formatRuDate(row.real_interview_date)}</td>
                    <td>{row.days_waiting}</td>
                    <td>
                      {tgUrl ? (
                        <a href={tgUrl} target="_blank" rel="noopener noreferrer">
                          {row.telegram_username}
                        </a>
                      ) : (
                        (row.telegram_username ?? '—')
                      )}
                    </td>
                    <td>{row.intern_manager_name ?? '—'}</td>
                    <td>{row.status_display ?? '—'}</td>
                    <td>{row.note?.trim() ? row.note : '—'}</td>
                    {canWrite ? (
                      <td className="action-buttons">
                        <Link
                          to={`/sad-intern/${row.id}/edit`}
                          className="btn-outline-primary btn-small"
                          title="Редактировать"
                        >
                          ✏️
                        </Link>
                        {isAdmin ? (
                          <button
                            type="button"
                            className="btn-outline-danger btn-small"
                            title="Удалить"
                            onClick={() => {
                              if (window.confirm('Удалить запись? Это действие нельзя отменить.')) {
                                onDelete(row.id)
                              }
                            }}
                          >
                            🗑️
                          </button>
                        ) : null}
                      </td>
                    ) : null}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </TableScroll>
      </div>
      <SadInternListMobileCards
        rows={group.results}
        canWrite={canWrite}
        isAdmin={isAdmin}
        onDelete={onDelete}
      />
      <Pagination
        currentPage={currentPage}
        totalPages={group.total_pages}
        onPageChange={(p) => onGroupPageChange(group.pagination_key, p)}
        showPageInput
      />
    </section>
  )
}

export default SadInternGroupSection
