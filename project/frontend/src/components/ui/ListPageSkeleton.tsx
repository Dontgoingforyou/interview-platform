import type { ReactNode } from 'react'

import DataTable from './DataTable'

/** Сетка карточек-скелетонов. */
export function ListPageMetricsSkeleton({ count }: { count: number }) {
  if (count <= 0) {
    return null
  }
  return (
    <div className="metrics-grid">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="metric-card">
          <div className="skeleton" style={{ height: '0.85rem', width: '55%', marginBottom: '0.75rem' }} />
          <div className="skeleton" style={{ height: '1.75rem', width: '40%' }} />
        </div>
      ))}
    </div>
  )
}

/** Блок «Поиск и фильтры» с полями-плейсхолдерами. */
export function ListPageFiltersSkeleton({ fields = 5 }: { fields?: number }) {
  return (
    <div className="interviews-subsection">
      <div className="interviews-subsection-card">
        <div className="interviews-subsection-head interns-filters-skeleton-head">
          <h2 className="interviews-section-title">Поиск и фильтры</h2>
        </div>
        <div className="interns-filters-skeleton">
          {Array.from({ length: fields }, (_, i) => (
            <div key={i} className="interns-filters-skeleton__cell">
              <div className="skeleton" style={{ height: '0.75rem', width: '35%', marginBottom: 6 }} />
              <div className="skeleton" style={{ height: 42, width: '100%', borderRadius: 8 }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export interface ListPageSkeletonProps {
  colCount: number
  tableHead: ReactNode
  /** Число карточек в сетке метрик; 0 — не показывать. */
  metricCardsCount?: number
  showFiltersSkeleton?: boolean
  filtersSkeletonFields?: number
  /** Два блока как ряд графиков на дашборде менеджеров. */
  showChartsRowSkeleton?: boolean
  skeletonRowCount?: number
  dataTableClassName?: string
  scrollClassName?: string
  className?: string
}

/** Скелетон первой загрузки: метрики, опционально фильтры и графики, таблица. */
function ListPageSkeleton({
  colCount,
  tableHead,
  metricCardsCount = 6,
  showFiltersSkeleton = false,
  filtersSkeletonFields = 5,
  showChartsRowSkeleton = false,
  skeletonRowCount = 10,
  dataTableClassName = 'data-table',
  scrollClassName,
  className,
}: ListPageSkeletonProps) {
  return (
    <div className={className} aria-busy="true" aria-label="Загрузка…">
      <ListPageMetricsSkeleton count={metricCardsCount} />
      {showChartsRowSkeleton ? (
        <div className="list-page-skeleton-charts">
          <div className="skeleton list-page-skeleton-chart" />
          <div className="skeleton list-page-skeleton-chart" />
        </div>
      ) : null}
      {showFiltersSkeleton ? <ListPageFiltersSkeleton fields={filtersSkeletonFields} /> : null}
      <DataTable className={dataTableClassName} scrollClassName={scrollClassName}>
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
      </DataTable>
    </div>
  )
}

export default ListPageSkeleton
