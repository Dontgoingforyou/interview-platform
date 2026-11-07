import type { ReactNode } from 'react'

import { ListPageFiltersSkeleton, ListPageMetricsSkeleton } from './ListPageSkeleton'
import { DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import TableScroll from './TableScroll'

export interface GroupedListPageSkeletonProps {
  metricCardsCount?: number
  showFiltersSkeleton?: boolean
  filtersSkeletonFields?: number
  /** Сколько блоков с заголовком и таблицей (месяцы / направления). */
  sectionCount?: number
  tableHead: ReactNode
  colCount: number
  skeletonRowCount?: number
  sectionClassName?: string
  tableClassName?: string
  scrollClassName?: string
  className?: string
}

/** Скелетон для страниц с группами таблиц (офферы по месяцам, «грустят» по направлениям). */
function GroupedListPageSkeleton({
  metricCardsCount = 6,
  showFiltersSkeleton = true,
  filtersSkeletonFields = 5,
  sectionCount = 3,
  tableHead,
  colCount,
  skeletonRowCount = 5,
  sectionClassName = 'offers-month-section month-section',
  tableClassName = `data-table offers-table ${DATA_TABLE_STICKY_LEADING}`,
  scrollClassName = 'table-scroll--plain offers-table-desktop',
  className,
}: GroupedListPageSkeletonProps) {
  return (
    <div className={className} aria-busy="true" aria-label="Загрузка…">
      <ListPageMetricsSkeleton count={metricCardsCount} />
      {showFiltersSkeleton ? <ListPageFiltersSkeleton fields={filtersSkeletonFields} /> : null}
      {Array.from({ length: sectionCount }, (_, s) => (
        <section key={s} className={sectionClassName}>
          <div
            className="skeleton"
            style={{ height: '1.25rem', width: 'min(220px, 50%)', marginBottom: '0.75rem' }}
          />
          <TableScroll className={scrollClassName}>
            <table className={tableClassName}>
              {tableHead}
              <tbody>
                {Array.from({ length: skeletonRowCount }, (_, i) => (
                  <tr key={i}>
                    {Array.from({ length: colCount }, (__, c) => (
                      <td key={c}>
                        <div className="skeleton" style={{ height: '1rem', minWidth: '3rem' }} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        </section>
      ))}
    </div>
  )
}

export default GroupedListPageSkeleton
