import type { UseQueryResult } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import Pagination from '../../Pagination'
import { TableScroll } from '../../ui'
import type { OfferListFilters, OfferListItem, OfferMonthGroupRow, PaginatedOffers } from '../../../types/offer'
import { getMonthLabel } from '../../../constants/monthChoices'
import { OFFER_MONTH_PAGE_SIZE } from '../../../api/offersApi'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../../utils/listPageDataRefreshing'
import { formatOfferAmountCell, offerTelegramHref } from '../../../utils/offers/offerListDisplay'
import OfferListMobileCard from './OfferListMobileCard'
import OfferListTableHead from './OfferListTableHead'

interface OfferMonthSectionProps {
  group: OfferMonthGroupRow
  listQuery: UseQueryResult<PaginatedOffers, Error>
  currentPage: number
  onPageChange: (page: number) => void
  filters: OfferListFilters
  onToggleSort: (field: string) => void
  isAdmin: boolean
  onDeleteOffer: (id: number) => void
}

/** Блок одного месяца: заголовок, таблица / карточки, пагинация */
function OfferMonthSection({
  group,
  listQuery,
  currentPage,
  onPageChange,
  filters,
  onToggleSort,
  isAdmin,
  onDeleteOffer,
}: OfferMonthSectionProps) {
  const title = `${getMonthLabel(group.month)} ${group.year}`
  const paginated = listQuery.data
  const results: OfferListItem[] = paginated?.results ?? []
  const count = paginated?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / OFFER_MONTH_PAGE_SIZE))

  if (listQuery.isError) {
    return (
      <section className="offers-month-section" aria-labelledby={`offers-month-${group.year}-${group.month}`}>
        <h3 id={`offers-month-${group.year}-${group.month}`}>{title}</h3>
        <p className="text-error">Не удалось загрузить данные за этот месяц.</p>
      </section>
    )
  }

  if (listQuery.isLoading && !paginated) {
    return (
      <section className="offers-month-section" aria-labelledby={`offers-month-${group.year}-${group.month}`}>
        <h3 id={`offers-month-${group.year}-${group.month}`}>{title}</h3>
        <p className="muted">Загрузка…</p>
      </section>
    )
  }

  return (
    <section
      className={withListDataRefreshingClass(
        'offers-month-section month-section',
        isListBackgroundRefetch(listQuery.isFetching, Boolean(paginated)),
      )}
      id={`month-${group.year}-${group.month}`}
      aria-labelledby={`offers-month-${group.year}-${group.month}`}
    >
      <h3 id={`offers-month-${group.year}-${group.month}`}>{title}</h3>
      {results.length === 0 ? (
        <p className="muted">Нет записей за этот период.</p>
      ) : (
        <>
          <div
            className="offers-mobile-cards"
            aria-label={`Офферы за ${title}, компактный вид`}
          >
            {results.map((row) => (
              <OfferListMobileCard
                key={row.id}
                row={row}
                isAdmin={isAdmin}
                onDelete={onDeleteOffer}
              />
            ))}
          </div>
          <TableScroll className="table-scroll--plain offers-table-desktop">
            <table
              className={`data-table offers-table ${DATA_TABLE_STICKY_LEADING}`}
            >
              <OfferListTableHead filters={filters} onToggleSort={onToggleSort} />
              <tbody>
                {results.map((row) => {
                  const tgUrl = offerTelegramHref(row.intern_telegram_username)
                  const tgLabel = row.intern_telegram_username?.trim() || '—'
                  return (
                    <tr key={row.id}>
                      <td>{row.id}</td>
                      <td>{row.intern_name}</td>
                      <td>{row.direction_name ?? '—'}</td>
                      <td>{row.company?.trim() ? row.company : '—'}</td>
                      <td>{formatOfferAmountCell(row.amount)}</td>
                      <td>
                        {tgUrl ? (
                          <a href={tgUrl} target="_blank" rel="noreferrer">
                            {tgLabel}
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="action-buttons interviews-col-actions">
                        {isAdmin ? (
                          <span className="interview-table-actions interview-table-actions--compact">
                            <Link
                              className="btn-outline-primary btn-small interviews-action-emoji"
                              title="Редактировать"
                              aria-label="Редактировать"
                              to={`/offers/${row.id}/edit`}
                            >
                              ✏️
                            </Link>
                            <button
                              type="button"
                              className="btn-outline-danger btn-small interviews-action-emoji"
                              title="Удалить"
                              aria-label="Удалить"
                              onClick={() => {
                                if (
                                  window.confirm('Удалить запись? Это действие нельзя отменить.')
                                ) {
                                  onDeleteOffer(row.id)
                                }
                              }}
                            >
                              🗑️
                            </button>
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </TableScroll>
        </>
      )}

      {count > OFFER_MONTH_PAGE_SIZE ? (
        <div className="month-pagination offers-month-pagination">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
            showPageInput
          />
        </div>
      ) : null}
    </section>
  )
}

export default OfferMonthSection
