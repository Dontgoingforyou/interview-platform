import type { ReactNode } from 'react'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import { INTERN_LIST_DESKTOP_COL_COUNT } from './internListConstants'

interface InternListSkeletonProps {
  tableHead: ReactNode
}

/** Скелетон: блок фильтров + таблица с шапкой из реальных колонок. */
function InternListSkeleton({ tableHead }: InternListSkeletonProps) {
  return (
    <div className="interns-page-skeleton" aria-busy="true" aria-label="Загрузка…">
      <div className="interviews-subsection">
        <div className="interviews-subsection-card">
          <div className="interviews-subsection-head interns-filters-skeleton-head">
            <h2 className="interviews-section-title">Поиск и фильтры</h2>
            <span className="interviews-subsection-toggle" aria-hidden>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </span>
          </div>
          <div className="interviews-collapsible-block">
            <div className="interviews-collapsible-block__inner">
              <div className="interns-filters-skeleton">
                {Array.from({ length: 6 }, (_, i) => (
                  <div key={i} className="interns-filters-skeleton__cell">
                    <div
                      className="skeleton"
                      style={{ height: '0.75rem', width: '35%', marginBottom: 6 }}
                    />
                    <div className="skeleton" style={{ height: 42, width: '100%', borderRadius: 8 }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      <TableScroll className="table-scroll--plain interns-table-desktop">
        <table className={`data-table data-table--interns ${DATA_TABLE_STICKY_LEADING}`}>
          {tableHead}
          <tbody>
            {Array.from({ length: 10 }, (_, i) => (
              <tr key={i}>
                {Array.from({ length: INTERN_LIST_DESKTOP_COL_COUNT }, (_, c) => (
                  <td key={c}>
                    <div className="skeleton" style={{ height: '1rem', minWidth: '3rem' }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </div>
  )
}

export default InternListSkeleton
